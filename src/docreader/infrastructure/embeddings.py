"""Embedding providers used to vectorize segment text."""

import asyncio
from pathlib import Path
from typing import Protocol

from docreader.core.embeddings import EMBEDDING_DIMENSIONS, EMBEDDING_MODEL


class EmbeddingError(Exception):
    """The embedding provider failed or returned an unexpected vector."""


class EmbeddingClient(Protocol):
    """A swappable source of fixed-size text embeddings."""

    dimensions: int

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector for each input, in the same order."""


class FastEmbedClient:
    """Local ONNX embeddings from the configured FastEmbed model."""

    def __init__(
        self,
        model_name: str = EMBEDDING_MODEL,
        dimensions: int = EMBEDDING_DIMENSIONS,
        cache_dir: Path | None = None,
    ) -> None:
        self.model_name = model_name
        self.dimensions = dimensions
        self.cache_dir = cache_dir
        self._model = None

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts without blocking the event loop."""
        if not texts:
            return []
        vectors = await asyncio.to_thread(self._embed_sync, texts)
        if len(vectors) != len(texts):
            raise EmbeddingError(
                "Embedding provider returned the wrong number of vectors"
            )
        for vector in vectors:
            if len(vector) != self.dimensions:
                raise EmbeddingError(
                    "Embedding provider returned a vector with the wrong dimensions"
                )
        return vectors

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        model = self._load_model()
        return [vector.tolist() for vector in model.embed(texts)]

    def _load_model(self):
        if self._model is None:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(
                model_name=self.model_name,
                cache_dir=str(self.cache_dir) if self.cache_dir else None,
            )
        return self._model


def create_embedder(
    model_name: str,
    dimensions: int,
    cache_dir: Path,
) -> FastEmbedClient:
    """Create the process-wide local embedding client."""
    return FastEmbedClient(
        model_name=model_name,
        dimensions=dimensions,
        cache_dir=cache_dir,
    )
