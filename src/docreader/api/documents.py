"""Document upload endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from docreader.application.ingest import persist_text_document
from docreader.core.config import get_settings
from docreader.ingestion.text import (
    DocumentTooLargeError,
    EmptyDocumentError,
    InvalidDocumentTextError,
    UnsupportedDocumentTypeError,
    prepare_text_upload,
)

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentCreated(BaseModel):
    """A document created from an accepted upload."""

    id: UUID
    title: str
    filename: str
    media_type: str
    version_number: int
    segment_count: int


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=DocumentCreated,
)
async def create_document(file: UploadFile, request: Request) -> DocumentCreated:
    """Store a text document and its extracted segments."""
    settings = get_settings()
    payload = await file.read()

    try:
        upload = prepare_text_upload(
            file.filename,
            payload,
            settings.max_upload_bytes,
        )
    except DocumentTooLargeError as error:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Document exceeds the upload size limit",
        ) from error
    except UnsupportedDocumentTypeError as error:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only .txt and .md documents are currently supported",
        ) from error
    except (EmptyDocumentError, InvalidDocumentTextError) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Document must contain valid UTF-8 text",
        ) from error

    session_factory = request.app.state.session_factory
    try:
        async with session_factory() as session:
            stored = await persist_text_document(session, upload)
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document could not be stored",
        ) from error

    return DocumentCreated(
        id=stored.document_id,
        title=stored.title,
        filename=stored.filename,
        media_type=stored.media_type,
        version_number=stored.version_number,
        segment_count=stored.segment_count,
    )
