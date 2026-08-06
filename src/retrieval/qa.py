from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from core.config import Settings
from retrieval.index import LocalEmbeddingIndex, SearchResult
from retrieval.llm import build_llm


@dataclass(frozen=True)
class AnswerResult:
    question: str
    answer: str
    retrieved_doc_ids: list[str]
    retrieved_contexts: list[str]
    retrieved_titles: list[str]


def _message_text(message: Any) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "\n".join(parts).strip()
    return str(content).strip()


def _context_payload(retrieved: list[SearchResult]) -> str:
    records = [
        {
            "paper_id": item.paper_id,
            "title": item.title,
            "content": item.content,
        }
        for item in retrieved
    ]
    return json.dumps(records, ensure_ascii=False, indent=2)


def answer_question(
    question: str,
    settings: Settings,
    index: LocalEmbeddingIndex,
    top_k: int | None = None,
) -> AnswerResult:
    # Building the configured provider first guarantees that missing credentials
    # or provider import/configuration errors stop the RAG run immediately.
    llm = build_llm(settings=settings, temperature=0.0)

    title_match = re.search(r"'([^']+)'", question)
    exact = index.lookup(title_match.group(1)) if title_match else None
    retrieved = index.search(question, top_k=top_k)
    if exact:
        exact_result = SearchResult(
            paper_id=exact["paper_id"],
            title=exact["title"],
            score=1.0,
            content=exact["content"],
            metadata=exact["metadata"],
        )
        deduped = [exact_result] + [item for item in retrieved if item.paper_id != exact_result.paper_id]
        retrieved = deduped[: (top_k or settings.top_k)]

    prompt = (
        "Answer the question using only the retrieved scholarly context below. "
        "Do not use outside knowledge. If the context does not support an answer, "
        "reply exactly: I don't know from the indexed corpus. Keep the answer concise.\n\n"
        f"Question:\n{question}\n\n"
        f"Retrieved scholarly context:\n{_context_payload(retrieved)}"
    )
    answer = _message_text(llm.invoke(prompt))
    if not answer:
        raise RuntimeError("The configured LLM returned an empty answer.")

    return AnswerResult(
        question=question,
        answer=answer,
        retrieved_doc_ids=[item.paper_id for item in retrieved],
        retrieved_contexts=[item.content for item in retrieved],
        retrieved_titles=[item.title for item in retrieved],
    )
