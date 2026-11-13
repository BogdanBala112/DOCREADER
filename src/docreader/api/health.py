"""Liveness and readiness endpoints."""

from typing import Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncEngine

from docreader.infrastructure.database import verify_database_connection

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Machine-readable service health response."""

    status: Literal["ok"]


@router.get("/live", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    """Report whether the API process is running."""
    return HealthResponse(status="ok")


@router.get("/ready", response_model=HealthResponse)
async def readiness(request: Request) -> HealthResponse:
    """Report whether required infrastructure is reachable."""
    engine: AsyncEngine = request.app.state.database_engine

    try:
        await verify_database_connection(engine)
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from error

    return HealthResponse(status="ok")
