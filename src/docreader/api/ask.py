"""Question answering retrieval endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError

from docreader.application.answer import answer_question
from docreader.application.search import search_segments
from docreader.core.config import get_settings
from docreader.infrastructure.chat import ChatError
from docreader.infrastructure.embeddings import EmbeddingError

router = APIRouter(tags=["ask"])


class AskRequest(BaseModel):
    """A natural-language question over the uploaded documents."""

    question: str = Field(min_length=1, max_length=2_000)
    limit: int | None = Field(default=None, ge=1, le=20)


class SegmentMatch(BaseModel):
    """One retrieved passage and its source location."""

    document_id: UUID
    title: str
    filename: str
    position: int
    content: str
    line_start: int
    line_end: int
    distance: float


class AskResponse(BaseModel):
    """A grounded answer and the passages used to write it."""

    answer: str
    matches: list[SegmentMatch]


@router.post("/ask", response_model=AskResponse)
async def ask(body: AskRequest, request: Request) -> AskResponse:
    """Find the stored passages most similar to a question."""
    question = body.question.strip()
    if not question:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Question must not be empty",
        )

    settings = get_settings()
    limit = body.limit or settings.retrieval_limit
    try:
        async with request.app.state.session_factory() as session:
            matches = await search_segments(
                session,
                request.app.state.embedder,
                question,
                limit,
                settings.retrieval_max_distance,
            )
    except EmbeddingError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Embedding provider is unavailable",
        ) from error
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search could not be completed",
        ) from error

    try:
        answer = await answer_question(request.app.state.chat, question, matches)
    except ChatError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat model is unavailable",
        ) from error

    return AskResponse(
        answer=answer,
        matches=[
            SegmentMatch(
                document_id=match.document_id,
                title=match.title,
                filename=match.filename,
                position=match.position,
                content=match.content,
                line_start=match.line_start,
                line_end=match.line_end,
                distance=match.distance,
            )
            for match in matches
        ],
    )
