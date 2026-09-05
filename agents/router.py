import json
import logging

from groq import Groq

from config.settings import settings
from tools.calculators import calculate_due_date, calculate_current_week, triage_symptom

logger = logging.getLogger(__name__)
client = Groq(api_key=settings.groq_api_key)

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "calculate_due_date",
            "description": "Calculate estimated due date from the last menstrual period date. Use when the user asks about their due date and provides a date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "last_period_date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                },
                "required": ["last_period_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_current_week",
            "description": "Calculate current pregnancy week and trimester from the last menstrual period date. Use when the user asks how many weeks pregnant they are and provides a date.",
            "parameters": {
                "type": "object",
                "properties": {
                    "last_period_date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                },
                "required": ["last_period_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "triage_symptom",
            "description": "Classify the urgency of a described symptom. Use when the user describes a specific symptom they're experiencing right now, to help gauge how urgently they should seek care.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symptom_description": {"type": "string", "description": "The symptom as described by the user"},
                },
                "required": ["symptom_description"],
            },
        },
    },
]

TOOL_FUNCTIONS = {
    "calculate_due_date": calculate_due_date,
    "calculate_current_week": calculate_current_week,
    "triage_symptom": triage_symptom,
}


def route_to_tool(question: str) -> dict | None:
    """Ask the LLM whether this question needs a tool. Returns the tool result dict, or None if no tool applies."""
    completion = client.chat.completions.create(
        model=settings.groq_model,
        messages=[{"role": "user", "content": question}],
        tools=TOOL_DEFINITIONS,
        tool_choice="auto",
        temperature=0,
        max_tokens=500,
        reasoning_effort="low",
    )

    message = completion.choices[0].message
    if not message.tool_calls:
        return None

    tool_call = message.tool_calls[0]
    func_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)

    logger.info("Routing to tool: %s with args %s", func_name, args)

    tool_fn = TOOL_FUNCTIONS.get(func_name)
    if not tool_fn:
        return None

    result = tool_fn(**args)
    return {"tool_used": func_name, "tool_result": result}