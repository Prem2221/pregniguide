from datetime import date, timedelta


def calculate_due_date(last_period_date: str) -> dict:
    """last_period_date in YYYY-MM-DD format. Uses Naegele's rule: LMP + 280 days."""
    lmp = date.fromisoformat(last_period_date)
    due_date = lmp + timedelta(days=280)
    return {
        "due_date": due_date.isoformat(),
        "method": "Naegele's rule (280 days from last menstrual period)",
        "note": "This is an estimate. Your healthcare provider's calculation, especially from an early ultrasound, may be more accurate.",
    }


def calculate_current_week(last_period_date: str) -> dict:
    lmp = date.fromisoformat(last_period_date)
    days_pregnant = (date.today() - lmp).days
    week = days_pregnant // 7
    day_in_week = days_pregnant % 7

    if week < 13:
        trimester = "first"
    elif week < 27:
        trimester = "second"
    else:
        trimester = "third"

    return {
        "current_week": week,
        "day_in_week": day_in_week,
        "trimester": trimester,
    }


TRIAGE_LEVELS = {
    "emergency": [
        "no fetal movement", "heavy bleeding", "severe abdominal pain",
        "seizure", "can't breathe", "chest pain",
    ],
    "urgent": [
        "moderate bleeding", "persistent headache", "blurred vision",
        "fever", "reduced fetal movement", "severe swelling",
    ],
    "routine": [
        "mild nausea", "mild back pain", "occasional cramping",
        "fatigue", "heartburn",
    ],
}


def triage_symptom(symptom_description: str) -> dict:
    """Simple keyword-based urgency classification — NOT a diagnostic tool."""
    text = symptom_description.lower()

    for level in ("emergency", "urgent", "routine"):
        for keyword in TRIAGE_LEVELS[level]:
            if keyword in text:
                return {"urgency": level, "matched_keyword": keyword}

    return {"urgency": "unknown", "matched_keyword": None}