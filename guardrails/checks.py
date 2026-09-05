import re


EMERGENCY_PATTERNS = [
    # Reduced/decreased fetal movement
    r"\b(not|hasn'?t|isn'?t|haven'?t)\s+(been\s+)?(moving|moved)\b",
    r"\b(baby|fetus)\s+(stopped|isn't|is not|hasn't|has not)\s+(moving|moved)\b",
    r"\b(can'?t|cannot)\s+feel\s+(the\s+)?baby\s+moving\b",

    # Bleeding / pain
    r"\bheavy bleeding\b",
    r"\bsevere pain\b",
    r"\bsevere abdominal pain\b",
    r"\bsevere stomach pain\b",

    # Breathing
    r"\bcan'?t breathe\b",
    r"\bcannot breathe\b",
    r"\btrouble breathing\b",
    r"\bdifficulty breathing\b",

    # Self-harm
    r"\bsuicid",
    r"\bharm (myself|my baby)\b",

    # Water breaking / possible fluid leakage
    r"\bwater broke\b",
    r"\bwaters broke\b",
    r"\bleaking fluid\b",
    r"\bamniotic fluid\b",
]


INJECTION_PATTERNS = [
    r"\bignore (all )?(previous|prior|above) instructions\b",
    r"\bignore (your )?(previous|prior|system) instructions\b",
    r"\bforget (all )?(previous|prior|above) instructions\b",
    r"\byou are now\b",
    r"\bsystem prompt\b",
    r"\bact as (an? )?(unrestricted|unfiltered|jailbroken|dan)\b",
    r"\bpretend (you (are|have) no|to have no) (rules|restrictions|guidelines)\b",
    r"\bdisregard your (rules|guidelines)\b",
    r"\bbypass (your )?(rules|restrictions|safety)\b",
]


def is_possible_emergency(text: str) -> bool:
    text = text.lower()
    return any(re.search(pattern, text) for pattern in EMERGENCY_PATTERNS)


def is_likely_injection(text: str) -> bool:
    text = text.lower()
    return any(re.search(pattern, text) for pattern in INJECTION_PATTERNS)


EMERGENCY_RESPONSE = (
    "⚠️ Based on what you've described, please contact your healthcare provider or "
    "emergency services right away — this isn't something to wait on. If you're in "
    "immediate danger, call your local emergency number now."
)


INJECTION_RESPONSE = (
    "I'm only able to help with pregnancy-related questions using trusted reference "
    "material. Could you rephrase your question?"
)