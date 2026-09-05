import pytest
from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.testing = True
    return app.test_client()


def test_home_page_loads(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_empty_question_returns_400(client):
    resp = client.post("/ask", json={"question": ""})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_missing_question_key_returns_400(client):
    resp = client.post("/ask", json={})
    assert resp.status_code == 400


def test_valid_question_returns_200(client):
    resp = client.post("/ask", json={"question": "What should I eat during pregnancy?"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "answer_markdown" in data
    assert "sources" in data


def test_emergency_question_returns_warning_without_llm_call(client):
    resp = client.post("/ask", json={"question": "the baby hasn't moved all day"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "emergency" in data["answer_markdown"].lower() or "immediately" in data["answer_markdown"].lower()


def test_style_mismatch_returns_redirect_message(client):
    resp = client.post("/ask", json={"question": "मुझे क्या खाना चाहिए", "language": "english"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert "english" in data["answer_markdown"].lower()