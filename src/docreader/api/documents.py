"""Document upload endpoints."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from docreader.application.documents import (
    delete_document,
    get_document,
    list_documents,
)
from docreader.application.ingest import persist_text_document
from docreader.core.config import get_settings
from docreader.infrastructure.embeddings import EmbeddingError
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
            stored = await persist_text_document(
                session,
                upload,
                request.app.state.embedder,
            )
    except EmbeddingError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding provider is unavailable",
        ) from error
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


class AssetInfo(BaseModel):
    """Metadata for one uploaded file version."""

    id: UUID
    version_number: int
    filename: str
    media_type: str
    byte_size: int
    segment_count: int
    created_at: datetime


class DocumentInfo(BaseModel):
    """A document with all its asset summaries."""

    id: UUID
    title: str
    created_at: datetime
    assets: list[AssetInfo]


def _to_document_info(doc) -> DocumentInfo:
    return DocumentInfo(
        id=doc.id,
        title=doc.title,
        created_at=doc.created_at,
        assets=[
            AssetInfo(
                id=a.id,
                version_number=a.version_number,
                filename=a.filename,
                media_type=a.media_type,
                byte_size=a.byte_size,
                segment_count=a.segment_count,
                created_at=a.created_at,
            )
            for a in doc.assets
        ],
    )


@router.get("", response_model=list[DocumentInfo])
async def list_documents_route(request: Request) -> list[DocumentInfo]:
    """Return all uploaded documents with their asset summaries."""
    try:
        async with request.app.state.session_factory() as session:
            docs = await list_documents(session)
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not load documents",
        ) from error
    return [_to_document_info(doc) for doc in docs]


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document_route(
    document_id: UUID, request: Request
) -> DocumentInfo:
    """Return one document and its asset summaries."""
    try:
        async with request.app.state.session_factory() as session:
            doc = await get_document(session, document_id)
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not load document",
        ) from error
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return _to_document_info(doc)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_route(
    document_id: UUID, request: Request
) -> None:
    """Delete a document and all its assets and segments."""
    try:
        async with request.app.state.session_factory() as session:
            found = await delete_document(session, document_id)
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document could not be deleted",
        ) from error
    if found:
        return Response(status_code = status.HTTP_204_NO_CONTENT)
    else:
        return Response(status_code = status.HTTP_404_NOT_FOUND)

