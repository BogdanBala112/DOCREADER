"""HTTP contract tests for semantic retrieval."""

from uuid import UUID

from fastapi.testclient import TestClient

from docreader.application.search import RetrievedSegment
from docreader.main import app

DOCUMENT_ID = UUID("0b6f6f0e-2f0a-4f8a-9c1d-6d5c2a9e8f11")


def test_ask_returns_matching_passages(monkeypatch) -> None:
    async def fake_search(_session, _embedder, question, limit, max_distance):
        assert question == "What is compound interest?"
        assert limit == 5
        assert max_distance == 0.45
        return [
            RetrievedSegment(
                document_id=DOCUMENT_ID,
                title="investment-topics",
                filename="investment-topics.md",
                position=3,
                content="Compound interest grows over time.",
                line_start=7,
                line_end=11,
                distance=0.12,
            )
        ]

    async def fake_answer(_chat, question, matches):
        assert question == "What is compound interest?"
        assert matches[0].filename == "investment-topics.md"
        return "Compound interest grows over time. [investment-topics.md:7-11]"

    monkeypatch.setattr("docreader.api.ask.search_segments", fake_search)
    monkeypatch.setattr("docreader.api.ask.answer_question", fake_answer)

    with TestClient(app) as client:
        response = client.post(
            "/ask",
            json={"question": " What is compound interest? "},
        )

    assert response.status_code == 200
    assert response.json() == {
        "answer": "Compound interest grows over time. [investment-topics.md:7-11]",
        "matches": [
            {
                "document_id": str(DOCUMENT_ID),
                "title": "investment-topics",
                "filename": "investment-topics.md",
                "position": 3,
                "content": "Compound interest grows over time.",
                "line_start": 7,
                "line_end": 11,
                "distance": 0.12,
            }
        ],
    }


def test_ask_rejects_a_blank_question() -> None:
    with TestClient(app) as client:
        response = client.post("/ask", json={"question": "   "})

    assert response.status_code == 422
    assert response.json()["detail"] == "Question must not be empty"
