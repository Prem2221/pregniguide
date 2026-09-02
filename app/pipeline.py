import json
import logging

from groq import Groq

from app.schemas import StructuredAnswer
from config.settings import settings
from prompts.system_prompt import SYSTEM_PROMPT
from rag.retriever import retrieve, format_context

logger = logging.getLogger(__name__)
client = Groq(api_key=settings.groq_api_key)


def _call_llm(question: str, context: str) -> StructuredAnswer:
    user_message = f"Context:\n{context}\n\nQuestion: {question}"

    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=1500,
        reasoning_effort="low",
        response_format={"type": "json_object"},
    )

    raw = completion.choices[0].message.content
    return StructuredAnswer.model_validate(json.loads(raw))


def answer_question(question: str) -> dict:
    docs = retrieve(question, k=4)
    context = format_context(docs)

    try:
        structured = _call_llm(question, context)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("Malformed structured output, retrying once: %s", e)
        structured = _call_llm(question, context)  # one retry — LLM JSON output occasionally malformed

    sources = [{"source": d.metadata["source"], "page": d.metadata["page_number"]} for d in docs]

    return {
        "answer_markdown": structured.answer_markdown,
        "comparison": structured.comparison.model_dump() if structured.comparison else None,
        "follow_up_questions": structured.follow_up_questions,
        "sources": sources,
    }