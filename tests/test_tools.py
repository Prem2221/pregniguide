from tools.calculators import calculate_due_date, calculate_current_week, triage_symptom


def test_calculate_due_date():
    result = calculate_due_date("2026-01-01")
    assert result["due_date"] == "2026-10-08"


def test_triage_emergency_symptom():
    result = triage_symptom("I have no fetal movement today")
    assert result["urgency"] == "emergency"


def test_triage_routine_symptom():
    result = triage_symptom("I have mild nausea")
    assert result["urgency"] == "routine"


def test_triage_unknown_symptom():
    result = triage_symptom("my elbow hurts")
    assert result["urgency"] == "unknown"