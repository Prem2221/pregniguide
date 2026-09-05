import json
import logging

from groq import Groq

from app.language import matches_selected_style, translate_to_english, restyle_response
from app.memory import get_history, add_turn
from app.schemas import StructuredAnswer
from agents.router import route_to_tool
from config.settings import settings
from guardrails.checks import (
    is_possible_emergency, is_likely_injection,
    EMERGENCY_RESPONSE, INJECTION_RESPONSE,
)
from prompts.system_prompt import SYSTEM_PROMPT
from rag.retriever import retrieve, format_context

logger = logging.getLogger(__name__)
client = Groq(api_key=settings.groq_api_key)

STYLE_MISMATCH_MESSAGES = {
    "english": "Please type your question in plain English, since that's what you selected. 🙏",
    "hinglish": "Please type your question in Hinglish or English, since that's what you selected. Kripya apna sawaal Hinglish mein poochhein. 🙏",
    "manglish": "Please type your question in Manglish or English, since that's what you selected. Ningalude chodyam Manglish il type cheyyu. 🙏",
}


def _empty_result(answer: str, language: str) -> dict:
    return {
        "answer_markdown": answer,
        "comparison": None,
        "follow_up_questions": [],
        "sources": [],
        "detected_language": language,
    }


def _call_llm(question: str, context: str, history: list[dict]) -> StructuredAnswer:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"})

    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=0.2,
        max_tokens=1500,
        reasoning_effort="low",
        response_format={"type": "json_object"},
    )
    raw = completion.choices[0].message.content
    return StructuredAnswer.model_validate(json.loads(raw))


def _format_tool_response(tool_result: dict, session_id: str, language: str) -> dict:
    tool_name = tool_result["tool_used"]
    result = tool_result["tool_result"]

    if tool_name == "calculate_due_date":
        answer = f"📅 Based on your last period date, your estimated due date is **{result['due_date']}**.\n\n_{result['note']}_"
    elif tool_name == "calculate_current_week":
        answer = f"🤰 You're currently around **week {result['current_week']}**, day {result['day_in_week']} — in your **{result['trimester']} trimester**."
    elif tool_name == "triage_symptom":
        urgency_labels = {
            "emergency": "🚨 This sounds urgent — please contact your healthcare provider or emergency services right away.",
            "urgent": "⚠️ This is worth contacting your healthcare provider about soon, today if possible.",
            "routine": "This is commonly experienced and usually not urgent, but mention it at your next appointment.",
            "unknown": "I'm not able to classify this symptom's urgency confidently — please describe it to your healthcare provider.",
        }
        answer = urgency_labels[result["urgency"]]
    else:
        answer = "I found relevant information but couldn't format it properly."

    if language != "english":
        answer = restyle_response(answer, language)

    result_dict = _empty_result(answer, language)
    result_dict["tool_used"] = tool_name
    return result_dict


def answer_question(question: str, session_id: str, language: str = "english") -> dict:
    if is_possible_emergency(question):
        return _empty_result(EMERGENCY_RESPONSE, language)

    if is_likely_injection(question):
        return _empty_result(INJECTION_RESPONSE, language)

    if not matches_selected_style(question, language):
        return _empty_result(STYLE_MISMATCH_MESSAGES[language], language)

    tool_result = route_to_tool(question)
    if tool_result:
        return _format_tool_response(tool_result, session_id, language)

    query_for_retrieval = translate_to_english(question) if language != "english" else question

    history = get_history(session_id)
    docs = retrieve(query_for_retrieval, k=4)
    context = format_context(docs)

    try:
        structured = _call_llm(query_for_retrieval, context, history)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("Malformed structured output, retrying once: %s", e)
        structured = _call_llm(query_for_retrieval, context, history)

    add_turn(session_id, "user", query_for_retrieval)
    add_turn(session_id, "assistant", structured.answer_markdown)

    answer_markdown = structured.answer_markdown
    follow_ups = structured.follow_up_questions

    if language != "english":
        answer_markdown = restyle_response(answer_markdown, language)
        follow_ups = [restyle_response(q, language) for q in follow_ups]

    sources = [{"source": d.metadata["source"], "page": d.metadata["page_number"]} for d in docs]

    return {
        "answer_markdown": answer_markdown,
        "comparison": structured.comparison.model_dump() if structured.comparison else None,
        "follow_up_questions": follow_ups,
        "sources": sources,
        "detected_language": language,
    }


def stream_answer(question: str, session_id: str, language: str = "english"):
    """Generator yielding newline-delimited JSON chunks.
    Streams token-by-token only for the English RAG path; all other paths
    (guardrails, tools, style mismatch, Hinglish/Manglish) yield one final
    chunk, since those either need no LLM call or need a restyle pass that
    can't be streamed cleanly.
    """

    def _final(result: dict) -> str:
        return json.dumps({"type": "final", "data": result}) + "\n"

    if is_possible_emergency(question):
        yield _final(_empty_result(EMERGENCY_RESPONSE, language))
        return

    if is_likely_injection(question):
        yield _final(_empty_result(INJECTION_RESPONSE, language))
        return

    if not matches_selected_style(question, language):
        yield _final(_empty_result(STYLE_MISMATCH_MESSAGES[language], language))
        return

    tool_result = route_to_tool(question)
    if tool_result:
        yield _final(_format_tool_response(tool_result, session_id, language))
        return

    query_for_retrieval = translate_to_english(question) if language != "english" else question
    history = get_history(session_id)
    docs = retrieve(query_for_retrieval, k=4)
    context = format_context(docs)
    sources = [{"source": d.metadata["source"], "page": d.metadata["page_number"]} for d in docs]

    if language != "english":
        # Restyle pass can't be streamed — full generation, then one final chunk
        structured = _call_llm(query_for_retrieval, context, history)
        add_turn(session_id, "user", query_for_retrieval)
        add_turn(session_id, "assistant", structured.answer_markdown)

        answer = restyle_response(structured.answer_markdown, language)
        follow_ups = [restyle_response(q, language) for q in structured.follow_up_questions]

        yield _final({
            "answer_markdown": answer,
            "comparison": structured.comparison.model_dump() if structured.comparison else None,
            "follow_up_questions": follow_ups,
            "sources": sources,
            "detected_language": language,
        })
        return

    # English path: real token-by-token streaming.
    # Note: dropping comparison tables and follow-up questions here — those
    # need structured JSON output, which doesn't stream cleanly. Trade-off:
    # faster perceived response, at the cost of those two features on this path.
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({
        "role": "user",
        "content": f"Context:\n{context}\n\nQuestion: {query_for_retrieval}\n\n"
                   f"Respond in plain markdown text only, no JSON wrapper, for this request.",
    })

    stream = client.chat.completions.create(
        model=settings.groq_model,
        messages=messages,
        temperature=0.2,
        max_tokens=1500,
        reasoning_effort="low",
        stream=True,
    )

    full_answer = ""
    for chunk in stream:
        delta = chunk.choices[0].delta.content or ""
        if delta:
            full_answer += delta
            yield json.dumps({"type": "chunk", "text": delta}) + "\n"

    add_turn(session_id, "user", query_for_retrieval)
    add_turn(session_id, "assistant", full_answer)

    yield _final({
        "answer_markdown": full_answer,
        "comparison": None,
        "follow_up_questions": [],
        "sources": sources,
        "detected_language": language,
    })