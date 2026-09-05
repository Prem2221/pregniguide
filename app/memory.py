from collections import defaultdict

# In-memory store: {session_id: [{"role": "user"/"assistant", "content": "..."}]}
# Simple for a personal project; would move to Redis/SQLite for real multi-instance deployment.
_sessions: dict[str, list[dict]] = defaultdict(list)

MAX_TURNS = 6  # keep last 6 exchanges to bound context size


def get_history(session_id: str) -> list[dict]:
    return _sessions[session_id]


def add_turn(session_id: str, role: str, content: str) -> None:
    _sessions[session_id].append({"role": role, "content": content})
    _sessions[session_id] = _sessions[session_id][-MAX_TURNS * 2:]