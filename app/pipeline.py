from groq import Groq

from config.settings import settings
from prompts.system_prompt import SYSTEM_PROMPT
from rag.retriever import retrieve, format_context

client = Groq(api_key=settings.groq_api_key)


def answer_question(question: str) -> dict:
    docs = retrieve(question, k=4)
    context = format_context(docs)

    user_message = f"""Context:
{context}

Question: {question}"""

    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.2,
        max_tokens=1500,
        reasoning_effort="low",
    )

    answer = completion.choices[0].message.content.strip()
    sources = [
        {"source": d.metadata["source"], "page": d.metadata["page_number"]}
        for d in docs
    ]

    return {"answer": answer, "sources": sources}