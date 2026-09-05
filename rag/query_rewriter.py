from groq import Groq

from config.settings import settings

_client = Groq(api_key=settings.groq_api_key)


def rewrite_query(question: str) -> str:
    """Expand a short/vague question into a more search-friendly query."""
    prompt = f"""Rewrite this question as a clear, specific search query for retrieving \
relevant pregnancy health information. Keep it short (under 20 words). Respond with ONLY \
the rewritten query, no explanation.

Question: {question}"""

    completion = _client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=200,
        reasoning_effort="low",
    )
    return completion.choices[0].message.content.strip()