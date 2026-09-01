import logging

from flask import Blueprint, jsonify, request

from app.pipeline import answer_question

logger = logging.getLogger(__name__)

bp = Blueprint("api", __name__)


@bp.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()

    if not question:
        return jsonify({"error": "Please provide a question."}), 400

    try:
        result = answer_question(question)
        return jsonify(result), 200
    except Exception:
        logger.exception("Failed to answer question: %s", question)
        return jsonify({"error": "Something went wrong while generating an answer. Please try again."}), 500