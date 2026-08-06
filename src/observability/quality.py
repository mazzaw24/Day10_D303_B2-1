from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import write_json


def _check(name: str, dimension: str, observed: Any, expectation: str, passed: bool) -> dict[str, Any]:
    return {
        "name": name,
        "dimension": dimension,
        "observed": observed,
        "expectation": expectation,
        "passed": bool(passed),
    }


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    total = int(len(df))
    ids = df.get("paper_id", pd.Series(dtype="object")).fillna("").astype(str)
    titles = df.get("title", pd.Series(dtype="object")).fillna("").astype(str)
    summaries = df.get("summary", pd.Series(dtype="object")).fillna("").astype(str)
    embedding_text = df.get("text_for_embedding", pd.Series(dtype="object")).fillna("").astype(str)
    summary_chars = pd.to_numeric(df.get("summary_chars", summaries.str.len()), errors="coerce").fillna(0)
    ages = pd.to_numeric(df.get("age_days", pd.Series([0] * total)), errors="coerce").fillna(10**9)

    checks = [
        _check("minimum_row_count", "volume", total, ">= 8", total >= 8),
        _check("paper_id_complete", "completeness", int((ids.str.strip() != "").sum()), f"== {total}", bool((ids.str.strip() != "").all())),
        _check("paper_id_unique", "uniqueness", int(ids.nunique()), f"== {total}", bool(ids.is_unique)),
        _check("title_complete", "completeness", int((titles.str.strip() != "").sum()), f"== {total}", bool((titles.str.strip() != "").all())),
        _check("summary_complete", "completeness", int((summaries.str.strip() != "").sum()), f"== {total}", bool((summaries.str.strip() != "").all())),
        _check("summary_min_length", "validity", int((summary_chars >= 80).sum()), f"== {total}", bool((summary_chars >= 80).all())),
        _check("embedding_text_complete", "completeness", int((embedding_text.str.strip() != "").sum()), f"== {total}", bool((embedding_text.str.strip() != "").all())),
        _check(
            "fresh_row_ratio",
            "freshness",
            round(float((ages <= settings.freshness_threshold_days).mean()) if total else 0.0, 4),
            ">= 0.80",
            bool(total and (ages <= settings.freshness_threshold_days).mean() >= 0.8),
        ),
    ]
    passed = sum(1 for item in checks if item["passed"])
    payload = {
        "report_name": report_name,
        "total_rows": total,
        "success": passed == len(checks),
        "passed_checks": passed,
        "failed_checks": len(checks) - passed,
        "checks": checks,
    }
    write_json(settings.paths.quality_dir / f"{report_name}.json", payload)
    gx_payload = {
        "success": payload["success"],
        "statistics": {
            "evaluated_expectations": len(checks),
            "successful_expectations": passed,
            "unsuccessful_expectations": len(checks) - passed,
            "success_percent": round((passed / len(checks)) * 100, 2) if checks else 0.0,
        },
        "results": [
            {
                "expectation_config": {
                    "expectation_type": item["name"],
                    "kwargs": {"expectation": item["expectation"]},
                },
                "success": item["passed"],
                "result": {"observed_value": item["observed"]},
                "meta": {"dimension": item["dimension"]},
            }
            for item in checks
        ],
    }
    write_json(settings.paths.gx_dir / f"{report_name}_validation.json", gx_payload)
    return payload


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    published = pd.to_datetime(df.get("published"), errors="coerce", utc=True)
    ages = pd.to_numeric(df.get("age_days"), errors="coerce")
    total = int(len(df))
    stale_rows = int((ages > settings.freshness_threshold_days).sum())
    is_fresh = bool(total and stale_rows / total <= 0.2)
    payload = {
        "latest_published": published.max().date().isoformat() if total and published.notna().any() else None,
        "oldest_published": published.min().date().isoformat() if total and published.notna().any() else None,
        "freshness_threshold_days": settings.freshness_threshold_days,
        "stale_rows": stale_rows,
        "total_rows": total,
        "stale_ratio": round(stale_rows / total, 4) if total else 1.0,
        "is_fresh": is_fresh,
        "status": "fresh" if is_fresh else "stale",
    }
    write_json(Path(report_path), payload)
    return payload