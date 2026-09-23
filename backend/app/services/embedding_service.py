from __future__ import annotations

import hashlib
import logging
import re
from functools import lru_cache

import numpy as np

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Local embeddings with an always-available deterministic fallback.

    fastembed is preferred in full builds. The hashing fallback keeps local search
    operational on constrained/offline machines and in the lightweight test build.
    """

    def __init__(self) -> None:
        self.model_name = get_settings().embedding_model
        self.cache_dir = get_settings().data_dir / "models"
        self._model = None
        self._model_attempted = False
        self.dimensions = 384

    def _ensure_model(self) -> None:
        if self._model_attempted:
            return
        self._model_attempted = True
        try:
            from fastembed import TextEmbedding

            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._model = TextEmbedding(
                model_name=self.model_name,
                cache_dir=str(self.cache_dir),
                local_files_only=True,
            )
            logger.info("Loaded local embedding model %s", self.model_name)
        except Exception as exc:
            logger.warning("Using hashing embeddings: %s", exc)

    def embed(self, texts: list[str]) -> list[np.ndarray]:
        self._ensure_model()
        if self._model is not None:
            return [np.asarray(vector, dtype=np.float32) for vector in self._model.embed(texts)]
        return [self._hash_embedding(text) for text in texts]

    def _hash_embedding(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dimensions, dtype=np.float32)
        for token in re.findall(r"\w+", text.lower()):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest[:4], "little") % self.dimensions
            vector[index] += 1 if digest[4] % 2 == 0 else -1
        norm = np.linalg.norm(vector)
        return vector / norm if norm else vector

    @staticmethod
    def serialize(vector: np.ndarray) -> bytes:
        return np.asarray(vector, dtype=np.float32).tobytes()

    @staticmethod
    def deserialize(blob: bytes, dimensions: int) -> np.ndarray:
        return np.frombuffer(blob, dtype=np.float32, count=dimensions)

    @staticmethod
    def cosine(left: np.ndarray, right: np.ndarray) -> float:
        denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
        return float(np.dot(left, right) / denominator) if denominator else 0.0


@lru_cache
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
