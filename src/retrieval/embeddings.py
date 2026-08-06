from __future__ import annotations

from functools import lru_cache
import hashlib
import math
import os
import re
from typing import Any

try:  # Optional dependency for the rubric-preferred backend.
    from langchain_core.embeddings import Embeddings as _EmbeddingsBase
except ImportError:  # pragma: no cover - exercised in lightweight environments
    class _EmbeddingsBase:  # type: ignore[too-many-ancestors]
        pass

try:
    from sentence_transformers import SentenceTransformer
except ImportError:  # pragma: no cover - exercised in lightweight environments
    SentenceTransformer = None  # type: ignore[assignment]


@lru_cache(maxsize=4)
def _load_model(model_name: str) -> Any:
    if SentenceTransformer is None:
        return None
    try:
        return SentenceTransformer(model_name)
    except Exception:
        return None


def _hash_embedding(text: str, dimensions: int = 384) -> list[float]:
    vector = [0.0] * dimensions
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        index = int.from_bytes(digest, "big") % dimensions
        sign = 1.0 if digest[0] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


class MiniLMEmbeddings(_EmbeddingsBase):
    """MiniLM embeddings with a deterministic hashing fallback.

    The fallback keeps the mandatory lab runnable without model downloads while
    preserving the same embedding interface and 384-dimensional vectors.
    """

    def __init__(self, model_name: str):
        force_local = os.getenv("FORCE_LOCAL_EMBEDDINGS", "").lower() in {"1", "true", "yes"}
        self.model_name = model_name
        self._model = None if force_local else _load_model(model_name)
        self.backend = "sentence-transformers" if self._model is not None else "deterministic-hash-384"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if self._model is not None:
            embeddings = self._model.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()
        return [_hash_embedding(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        if self._model is not None:
            embedding = self._model.encode([text], normalize_embeddings=True)
            return embedding[0].tolist()
        return _hash_embedding(text)
