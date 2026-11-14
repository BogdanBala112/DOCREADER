"""HTTP contract tests for document upload."""

from uuid import UUID

from fastapi.testclient import TestClient

from docreader.application.ingest import StoredDocument
from docreader.main import app

DOCUMENT_ID = UUID("0b6f6f0e-2f0a-4f8a-9c1d-6d5c2a9e8f11")


def test_text_upload_returns_created_document(monkeypatch) -> None:
    async def fake_persist(_session, upload):
        assert upload.filename == "notes.txt"
        assert upload.segments[0].content == "Hello retrieval"
        return StoredDocument(
            document_id=DOCUMENT_ID,
            title="notes",
            filename="notes.txt",
            media_type="text/plain",
            version_number=1,
            segment_count=1,
        )

    monkeypatch.setattr(
        "docreader.api.documents.persist_text_document",
        fake_persist,
    )

    with TestClient(app) as client:
        response = client.post(
            "/documents",
            files={"file": ("notes.txt", b"Hello retrieval\n", "text/plain")},
        )

    assert response.status_code == 201
    assert response.json() == {
        "id": str(DOCUMENT_ID),
        "title": "notes",
        "filename": "notes.txt",
        "media_type": "text/plain",
        "version_number": 1,
        "segment_count": 1,
    }


def test_markdown_upload_is_accepted(monkeypatch) -> None:
    async def fake_persist(_session, upload):
        assert upload.media_type == "text/markdown"
        return StoredDocument(
            document_id=DOCUMENT_ID,
            title="guide",
            filename="guide.md",
            media_type="text/markdown",
            version_number=1,
            segment_count=1,
        )

    monkeypatch.setattr(
        "docreader.api.documents.persist_text_document",
        fake_persist,
    )

    with TestClient(app) as client:
        response = client.post(
            "/documents",
            files={"file": ("guide.md", b"# Guide\n", "text/markdown")},
        )

    assert response.status_code == 201
    assert response.json()["media_type"] == "text/markdown"


def test_unsupported_document_type_is_refused() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/documents",
            files={"file": ("report.pdf", b"%PDF", "application/pdf")},
        )

    assert response.status_code == 415
    assert response.json()["detail"] == (
        "Only .txt and .md documents are currently supported"
    )


def test_empty_document_is_refused() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/documents",
            files={"file": ("empty.txt", b" \n", "text/plain")},
        )

    assert response.status_code == 422
    assert response.json()["detail"] == "Document must contain valid UTF-8 text"
