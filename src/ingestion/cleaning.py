from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord


CLEAN_COLUMNS = [
    "paper_id",
    "title",
    "summary",
    "authors",
    "categories",
    "primary_category",
    "published",
    "updated",
    "abs_url",
    "pdf_url",
    "comment",
    "authors_joined",
    "categories_joined",
    "summary_chars",
    "age_days",
    "text_for_embedding",
]


def _string_list(value: Any) -> list[str]:
    values = value if isinstance(value, list) else [value]
    normalized = [normalize_whitespace(str(item)) for item in values]
    return [item for item in normalized if item]


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    if run_date.tzinfo is None:
        run_date = run_date.replace(tzinfo=UTC)
    rows: list[dict[str, Any]] = []
    for record in records:
        paper_id = normalize_whitespace(record.paper_id).lower()
        title = normalize_whitespace(record.title)
        summary = normalize_whitespace(record.summary)
        if not paper_id or not title or len(summary) < 40:
            continue
        try:
            published_dt = pd.to_datetime(record.published, utc=True)
        except (TypeError, ValueError):
            continue
        if pd.isna(published_dt):
            continue
        updated_dt = pd.to_datetime(record.updated or record.published, utc=True, errors="coerce")
        if pd.isna(updated_dt):
            updated_dt = published_dt
        age_days = max(0, int((run_date.date() - published_dt.date()).days))
        authors = _string_list(record.authors) or ["Unknown author"]
        categories = _string_list(record.categories) or ["Scholarly work"]
        authors_joined = ", ".join(authors)
        categories_joined = ", ".join(categories)
        rows.append(
            {
                "paper_id": paper_id,
                "title": title,
                "summary": summary,
                "authors": authors,
                "categories": categories,
                "primary_category": normalize_whitespace(record.primary_category) or categories[0],
                "published": published_dt.date().isoformat(),
                "updated": updated_dt.date().isoformat(),
                "abs_url": normalize_whitespace(record.abs_url),
                "pdf_url": normalize_whitespace(record.pdf_url),
                "comment": normalize_whitespace(record.comment),
                "authors_joined": authors_joined,
                "categories_joined": categories_joined,
                "summary_chars": len(summary),
                "age_days": age_days,
                "text_for_embedding": (
                    f"Title: {title}\nAuthors: {authors_joined}\nCategories: {categories_joined}\n"
                    f"Published: {published_dt.date().isoformat()}\nSummary: {summary}"
                ),
            }
        )
    df = pd.DataFrame(rows, columns=CLEAN_COLUMNS)
    if df.empty:
        raise ValueError("Cleaning produced an empty dataset.")
    df = df.drop_duplicates(subset=["paper_id"], keep="first")
    df = df.sort_values(["published", "paper_id"], ascending=[False, True]).reset_index(drop=True)
    return df
