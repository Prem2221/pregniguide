import json
import logging

from groq import Groq

from config.settings import settings

logger = logging.getLogger(__name__)
client = Groq(api_key=settings.groq_api_key)

STYLE_DESCRIPTIONS = {
    "hinglish": "Hinglish (a casual mix of Hindi and English, written in Roman/English script, "
                "the way it's commonly typed by Hindi speakers in everyday texting)",
    "manglish": "Manglish (a casual mix of Malayalam and English, written in Roman/English script, "
                "the way it's commonly typed by Malayalam speakers in everyday texting)",
}


def matches_selected_style(text: str, language: str) -> bool:
    """Loose check: does the input roughly match the selected style?
    This is inherently fuzzier than clean language detection, since Hinglish/
    Manglish have no fixed grammar — we ask the LLM to judge loosely rather
    than pretend this can be precise."""
    if language == "english":
        prompt = f"""Is the following text written in plain English, with no Hindi or \
Malayalam words mixed in? Answer with only "yes" or "no".

Text: {text}"""
    else:
        style = STYLE_DESCRIPTIONS[language]
        prompt = f"""Is the following text roughly written in {style}, or plain English, or a \
reasonable mix that a {language} speaker might type? Be lenient — answer "no" only if it's \
clearly a different language entirely (e.g. written in Hindi/Malayalam script, or a totally \
unrelated language). Answer with only "yes" or "no".

Text: {text}"""

    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=200,
        reasoning_effort="low",
    )
    result = completion.choices[0].message.content.strip().lower()
    return "yes" in result


def translate_to_english(text: str) -> str:
    """Convert Hinglish/Manglish input into plain English for retrieval."""
    prompt = f"""The following text may be in Hinglish, Manglish, or plain English. \
Translate/convert it into plain, clear English. Respond with ONLY the English text.

Text: {text}"""

    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=500,
        reasoning_effort="low",
    )
    return completion.choices[0].message.content.strip()


def restyle_response(text: str, language: str) -> str:
    """Rewrite an English answer into the target casual style."""
    if language == "english":
        return text

    style = STYLE_DESCRIPTIONS[language]
    prompt = f"""Rewrite the following text in {style}. Keep all the factual content, \
formatting (markdown, bullet points, emojis), and meaning exactly the same — only change \
the language style to be natural, casual {language}, as someone would actually type it. \
Respond with ONLY the rewritten text.

Text: {text}"""

    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1500,
        reasoning_effort="low",
    )
    return completion.choices[0].message.content.strip()