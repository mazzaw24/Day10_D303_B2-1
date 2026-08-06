from __future__ import annotations

from dataclasses import dataclass
import math
import os
from pathlib import Path
from typing import Any

import pandas as pd

try:
    import chromadb
except ImportError:  # pragma: no cover - current lightweight runtime
    chromadb = None  # type: ignore[assignment]

from core.config import Settings
from core.utils import read_json, safe_slug, write_json
from retrieval.embeddings import MiniLMEmbeddings


@dataclass(frozen=True)
class SearchResult:
    paper_id: str
    title: str
    score: float
    content: str
    metadata: dict[str, Any]


def _cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


class LocalEmbeddingIndex:
    def __init__(
        self,
        settings: Settings,
        collection_name: str,
        documents: list[dict[str, Any]],
        persist_path: Path,
        backend: str,
        vectors: list[list[float]] | None = None,
    ):
        self.settings = settings
        self.collection_name = collection_name
        self.documents = documents
        self.persist_path = persist_path
        self.embedding_model = MiniLMEmbeddings(settings.embedding_model)
        self.embedding_backend = backend
        self.vectors = vectors or []
        self.client = None
        self.collection = None
        if backend == "chroma":
            if chromadb is None:
                raise RuntimeError("This index manifest requires ChromaDB, but chromadb is not installed.")
            self.client = chromadb.PersistentClient(path=str(persist_path))
            self.collection = self.client.get_collection(name=collection_name)
        self.documents_by_paper_id = {document["paper_id"].lower(): document for document in documents}
        self.documents_by_title = {document["title"].lower(): document for document in documents}

    @staticmethod
    def _build_documents(df: pd.DataFrame) -> list[dict[str, Any]]:
        documents: list[dict[str, Any]] = []
        for index, row in enumerate(df.to_dict(orient="records")):
            documents.append(
                {
                    "record_id": f"{row['paper_id']}::{index}",
                    "paper_id": row["paper_id"],
                    "title": row["title"],
                    "content": row["text_for_embedding"],
                    "metadata": {
                        "paper_id": row["paper_id"],
                        "title": row["title"],
                        "published": row["published"],
                        "authors_joined": row["authors_joined"],
                        "categories_joined": row["categories_joined"],
                        "summary": row["summary"],
                        "abs_url": row["abs_url"],
                        "pdf_url": row["pdf_url"],
                    },
                }
            )
        return documents

    @staticmethod
    def _derive_collection_name(settings: Settings, embeddings_output_path: Path | None) -> str:
        if embeddings_output_path is None:
            return settings.baseline_collection_name
        name_map = {
            settings.paths.embeddings_json.resolve(): settings.baseline_collection_name,
            settings.paths.corrupted_embeddings_json.resolve(): settings.corrupted_collection_name,
            settings.paths.repaired_embeddings_json.resolve(): settings.repaired_collection_name,
        }
        return name_map.get(embeddings_output_path.resolve(), safe_slug(embeddings_output_path.stem))

    @classmethod
    def build(
        cls,
        df: pd.DataFrame,
        settings: Settings,
        embeddings_output_path: Path | None = None,
    ) -> "LocalEmbeddingIndex":
        if df.empty:
            raise ValueError("Cannot build an embedding index from an empty dataframe.")
        collection_name = cls._derive_collection_name(settings, embeddings_output_path)
        documents = cls._build_documents(df)
        if not all(document["content"].strip() for document in documents):
            # Keep corrupted rows observable while excluding empty documents from the index.
            documents = [document for document in documents if document["content"].strip()]
        if not documents:
            raise ValueError("No non-empty embedding documents are available.")
        persist_path = settings.paths.chroma_dir
        persist_path.mkdir(parents=True, exist_ok=True)
        embedding_model = MiniLMEmbeddings(settings.embedding_model)
        vectors = embedding_model.embed_documents([document["content"] for document in documents])

        force_local = os.getenv("FORCE_LOCAL_EMBEDDINGS", "").lower() in {"1", "true", "yes"}
        use_chroma = chromadb is not None and not force_local
        backend = "chroma" if use_chroma else "local-cosine"
        if use_chroma:
            client = chromadb.PersistentClient(path=str(persist_path))
            try:
                client.delete_collection(name=collection_name)
            except Exception:
                pass
            collection = client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})
            collection.add(
                ids=[document["record_id"] for document in documents],
                embeddings=vectors,
                documents=[document["content"] for document in documents],
                metadatas=[document["metadata"] for document in documents],
            )

        manifest_path = embeddings_output_path or settings.paths.embeddings_json
        write_json(
            manifest_path,
            {
                "backend": backend,
                "embedding_backend": embedding_model.backend,
                "embedding_model": settings.embedding_model,
                "persist_path": str(persist_path),
                "collection_name": collection_name,
                "documents": documents,
                "vectors": vectors if backend == "local-cosine" else None,
            },
        )
        return cls(settings, collection_name, documents, persist_path, backend, vectors if backend == "local-cosine" else None)

    @classmethod
    def load(cls, settings: Settings, embeddings_path: Path | None = None) -> "LocalEmbeddingIndex":
        payload = read_json(embeddings_path or settings.paths.embeddings_json)
        return cls(
            settings=settings,
            collection_name=payload["collection_name"],
            documents=payload["documents"],
            persist_path=Path(payload["persist_path"]),
            backend=payload["backend"],
            vectors=payload.get("vectors") or [],
        )

    def search(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        limit = min(top_k or self.settings.top_k, len(self.documents))
        if limit <= 0:
            return []
        query_embedding = self.embedding_model.embed_query(query)
        if self.embedding_backend == "chroma":
            assert self.collection is not None
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                include=["documents", "metadatas", "distances"],
            )
            ids = results.get("ids", [[]])[0]
            contents = results.get("documents", [[]])[0]
            metadatas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            return [
                SearchResult(
                    paper_id=str(metadata["paper_id"]),
                    title=str(metadata["title"]),
                    score=max(0.0, 1.0 - float(distance or 0.0)),
                    content=str(content),
                    metadata=dict(metadata),
                )
                for record_id, content, metadata, distance in zip(ids, contents, metadatas, distances, strict=False)
                if record_id and content and metadata
            ]

        ranked = sorted(
            (
                (_cosine(query_embedding, vector), document)
                for vector, document in zip(self.vectors, self.documents, strict=False)
            ),
            key=lambda item: (item[0], item[1]["paper_id"]),
            reverse=True,
        )[:limit]
        return [
            SearchResult(
                paper_id=document["paper_id"],
                title=document["title"],
                score=max(0.0, float(score)),
                content=document["content"],
                metadata=document["metadata"],
            )
            for score, document in ranked
        ]

    def lookup(self, value: str) -> dict[str, Any] | None:
        needle = value.strip().lower()
        return self.documents_by_paper_id.get(needle) or self.documents_by_title.get(needle)
