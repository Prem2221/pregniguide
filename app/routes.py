import json
import logging
import uuid

from flask import Blueprint, jsonify, request, Response

from app.pipeline import answer_question, stream_answer

logger = logging.getLogger(__name__)
bp = Blueprint("api", __name__)


@bp.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())
    language = data.get("language", "english")

    if language not in ("english", "hinglish", "manglish"):
        language = "english"

    if not question:
        return jsonify({"error": "Please provide a question."}), 400

    try:
        result = answer_question(question, session_id, language)
        result["session_id"] = session_id
        return jsonify(result), 200
    except Exception:
        logger.exception("Failed to answer question: %s", question)
        return jsonify({"error": "Something went wrong while generating an answer. Please try again."}), 500


@bp.route("/ask-stream", methods=["POST"])
def ask_stream():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())
    language = data.get("language", "english")

    if language not in ("english", "hinglish", "manglish"):
        language = "english"

    if not question:
        return jsonify({"error": "Please provide a question."}), 400

    def generate():
        try:
            for line in stream_answer(question, session_id, language):
                yield line
        except Exception:
            logger.exception("Streaming failed for question: %s", question)
            yield json.dumps({"type": "error", "message": "Something went wrong. Please try again."}) + "\n"

    return Response(generate(), mimetype="application/x-ndjson")