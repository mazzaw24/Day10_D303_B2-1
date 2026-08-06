from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from html import unescape
from pathlib import Path
import os
import re
import time
from typing import Any

import requests

from core.config import Settings
from core.utils import normalize_whitespace, read_json, write_json


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    summary: str
    authors: list[str]
    categories: list[str]
    primary_category: str
    published: str
    updated: str
    abs_url: str
    pdf_url: str
    comment: str


def _strip_markup(value: Any) -> str:
    text = unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    return normalize_whitespace(text)


def _first_text(value: Any) -> str:
    if isinstance(value, list):
        return _strip_markup(value[0]) if value else ""
    return _strip_markup(value)


def _date_from_parts(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    parts = value.get("date-parts", [[]])
    if not parts or not parts[0]:
        return ""
    numbers = list(parts[0]) + [1, 1]
    try:
        return datetime(int(numbers[0]), int(numbers[1]), int(numbers[2]), tzinfo=UTC).date().isoformat()
    except (TypeError, ValueError):
        return ""


def _updated_date(item: dict[str, Any], published: str) -> str:
    for key in ("indexed", "created", "deposited"):
        candidate = item.get(key)
        if isinstance(candidate, dict):
            timestamp = candidate.get("date-time")
            if timestamp:
                try:
                    return datetime.fromisoformat(str(timestamp).replace("Z", "+00:00")).date().isoformat()
                except ValueError:
                    pass
            date_value = _date_from_parts(candidate)
            if date_value:
                return date_value
    return published


def parse_crossref_payload(payload: dict) -> list[PaperRecord]:
    items = payload.get("message", {}).get("items", [])
    if not isinstance(items, list):
        raise ValueError("Crossref payload must contain message.items as a list.")

    records: list[PaperRecord] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        paper_id = normalize_whitespace(str(item.get("DOI") or "")).lower()
        title = _first_text(item.get("title"))
        summary = _strip_markup(item.get("abstract"))
        if not paper_id or not title or not summary or paper_id in seen:
            continue

        authors: list[str] = []
        for author in item.get("author") or []:
            if not isinstance(author, dict):
                continue
            name = normalize_whitespace(f"{author.get('given', '')} {author.get('family', '')}")
            if name:
                authors.append(name)
        if not authors:
            authors = ["Unknown author"]

        categories = [normalize_whitespace(str(value)) for value in (item.get("subject") or [])]
        categories = [value for value in categories if value]
        if not categories:
            categories = [normalize_whitespace(str(item.get("type") or "Scholarly work"))]

        published = ""
        for key in ("published", "published-print", "published-online", "issued", "created"):
            published = _date_from_parts(item.get(key))
            if published:
                break
        if not published:
            created = item.get("created") or {}
            timestamp = created.get("date-time") if isinstance(created, dict) else None
            try:
                published = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00")).date().isoformat()
            except (TypeError, ValueError):
                continue

        pdf_url = ""
        for link in item.get("link") or []:
            if not isinstance(link, dict):
                continue
            content_type = str(link.get("content-type") or "").lower()
            candidate = str(link.get("URL") or "")
            if candidate and ("pdf" in content_type or candidate.lower().endswith(".pdf")):
                pdf_url = candidate
                break

        abs_url = str(item.get("URL") or f"https://doi.org/{paper_id}")
        comment = _first_text(item.get("container-title")) or _first_text(item.get("publisher"))
        records.append(
            PaperRecord(
                paper_id=paper_id,
                title=title,
                summary=summary,
                authors=authors,
                categories=categories,
                primary_category=categories[0],
                published=published,
                updated=_updated_date(item, published),
                abs_url=abs_url,
                pdf_url=pdf_url,
                comment=comment,
            )
        )
        seen.add(paper_id)
    return records


def _offline_crossref_payload(max_results: int) -> dict[str, Any]:
    """Create a deterministic Crossref-shaped fixture for offline execution."""
    topics = [
        "retrieval quality monitoring",
        "data freshness in knowledge bases",
        "duplicate detection for vector stores",
        "evaluation of grounded question answering",
        "observability for machine learning pipelines",
        "repair of corrupted scholarly metadata",
        "hybrid dense and lexical retrieval",
        "agentic retrieval planning",
    ]
    base_date = datetime.now(UTC).date()
    items: list[dict[str, Any]] = []
    for index in range(max_results):
        topic = topics[index % len(topics)]
        date = base_date - timedelta(days=5 + index * 3)
        doi = f"10.9999/day10.rag.{index + 1:03d}"
        title = f"Study {index + 1} on {topic.title()} for Reliable RAG"
        abstract = (
            f"This scholarly metadata fixture examines {topic} in retrieval augmented generation systems. "
            f"The study reports controlled experiment {index + 1}, measurable quality signals, and a reproducible "
            "comparison between healthy, corrupted, and repaired data states."
        )
        items.append(
            {
                "DOI": doi,
                "title": [title],
                "abstract": f"<jats:p>{abstract}</jats:p>",
                "author": [
                    {"given": f"Researcher{index + 1}", "family": "Example"},
                    {"given": "Data", "family": "Observer"},
                ],
                "subject": ["Artificial Intelligence", "Information Retrieval", "Data Quality"],
                "published": {"date-parts": [[date.year, date.month, date.day]]},
                "created": {"date-time": f"{date.isoformat()}T00:00:00Z"},
                "URL": f"https://doi.org/{doi}",
                "link": [{"URL": f"https://example.invalid/{index + 1}.pdf", "content-type": "application/pdf"}],
                "container-title": ["Journal of Reproducible RAG"],
                "type": "journal-article",
            }
        )
    return {
        "status": "ok",
        "message-type": "work-list",
        "message-version": "1.0.0",
        "offline_fixture": True,
        "offline_reason": "Crossref network access was unavailable; this payload preserves the Crossref schema for reproducible execution.",
        "message": {"items": items, "total-results": len(items)},
    }


def fetch_source_records(settings: Settings) -> list[PaperRecord]:
    params = {
        "query": settings.source_query,
        "filter": settings.source_filter,
        "rows": settings.max_results,
        "sort": "published",
        "order": "desc",
    }
    headers = {
        "User-Agent": "Day10DataObservabilityLab/1.0 (educational RAG pipeline)",
        "Accept": "application/json",
    }
    payload: dict[str, Any] | None = None
    last_error: Exception | None = None
    force_offline = os.getenv("FORCE_OFFLINE_SOURCE", "").lower() in {"1", "true", "yes"}
    if not force_offline:
        for attempt in range(4):
            try:
                response = requests.get("https://api.crossref.org/works", params=params, headers=headers, timeout=30)
                if response.status_code in {429, 500, 502, 503, 504}:
                    raise requests.HTTPError(f"Crossref temporary error {response.status_code}")
                response.raise_for_status()
                payload = response.json()
                payload["acquisition"] = {
                    "mode": "live_crossref_api",
                    "source_api": settings.source_api,
                    "query": settings.source_query,
                    "filter": settings.source_filter,
                    "rows": settings.max_results,
                }
                break
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt < 3:
                    time.sleep(0.5 * (2**attempt))
    else:
        last_error = RuntimeError("FORCE_OFFLINE_SOURCE enabled")

    if payload is None:
        payload = _offline_crossref_payload(settings.max_results)
        payload["fetch_error"] = f"{type(last_error).__name__}: {last_error}" if last_error else "unknown"
        payload["acquisition"] = {
            "mode": "offline_fixture",
            "source_api": settings.source_api,
            "query": settings.source_query,
            "filter": settings.source_filter,
            "rows": settings.max_results,
        }

    write_json(settings.paths.raw_api_response, payload)
    records = parse_crossref_payload(payload)
    if not records:
        raise RuntimeError("No valid Crossref records were available after parsing.")
    write_json(settings.paths.raw_records_json, [asdict(record) for record in records])
    return records


def load_raw_records(path: Path) -> list[PaperRecord]:
    payload = read_json(path)
    if not isinstance(payload, list):
        raise ValueError("Raw records snapshot must be a JSON list.")
    records: list[PaperRecord] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Each raw record must be a JSON object.")
        records.append(PaperRecord(**item))
    return records
