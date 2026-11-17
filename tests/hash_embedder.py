"""Deterministic embeddings for tests that exercise vector storage."""

import hashlib
import math


class HashEmbeddingClient:
    """Map tokens to a stable unit vector without calling a model."""

    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one normalized hashed vector per text."""
        return [_hash_vector(text, self.dimensions) for text in texts]


def _hash_vector(text: str, dimensions: int) -> list[float]:
    vector = [0.0] * dimensions
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode()).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]
