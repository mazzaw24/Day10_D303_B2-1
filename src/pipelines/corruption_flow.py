from __future__ import annotations

from typing import Any

import pandas as pd

from core.config import Settings, load_settings, normalized_provider, require_llm_credentials
from core.utils import now_utc, read_json, sha256_file, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from ingestion.cleaning import build_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report, generate_metrics_svg
from pipelines.phase1 import run_pipeline
from retrieval.index import LocalEmbeddingIndex


def _load_dataframe(path) -> pd.DataFrame:
    payload = read_json(path)
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"Expected a non-empty JSON-record dataset at {path}")
    return pd.DataFrame(payload)


def _assert_repair_matches_baseline(baseline: pd.DataFrame, repaired: pd.DataFrame) -> None:
    columns = [
        "paper_id",
        "title",
        "summary",
        "authors_joined",
        "categories_joined",
        "published",
        "text_for_embedding",
    ]
    left = baseline[columns].sort_values("paper_id").reset_index(drop=True)
    right = repaired[columns].sort_values("paper_id").reset_index(drop=True)
    if not left.equals(right):
        raise RuntimeError("Repair did not reproduce the baseline clean dataset from raw records.")


def run_corruption_pipeline(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or load_settings()
    require_llm_credentials(settings)
    prerequisites = [
        settings.paths.raw_records_json,
        settings.paths.clean_json,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
    ]
    if not all(path.exists() for path in prerequisites):
        run_pipeline(settings)

    frozen_hash = sha256_file(settings.paths.eval_testset)
    baseline_df = _load_dataframe(settings.paths.clean_json)
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    strict_backends = (
        baseline_metrics.get("answer_backend"),
        baseline_metrics.get("judge_backend"),
        baseline_metrics.get("ragas_backend"),
    )
    if strict_backends != ("configured_llm", "configured_llm", "configured_llm"):
        raise RuntimeError(
            "Corruption flow requires a strict configured-LLM baseline. "
            "Delete legacy baseline artifacts and rerun phase 1 with a valid API key."
        )
    if baseline_metrics.get("llm_provider") != normalized_provider(settings) or baseline_metrics.get(
        "llm_model"
    ) != settings.model_name:
        raise RuntimeError(
            "Baseline provider/model do not match the current corruption-flow configuration. "
            "Rerun phase 1 with the same provider and model."
        )
    if baseline_metrics.get("test_set_sha256") != frozen_hash:
        raise RuntimeError("Baseline metrics do not match the current frozen evaluation set.")

    corrupted_df = corrupt_clean_dataframe(baseline_df, settings.paths.corruption_log)
    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df, settings, settings.paths.corrupted_embeddings_json
    )
    corrupted_bundle = evaluate_pipeline(
        settings,
        corrupted_index,
        settings.paths.eval_testset,
        settings.paths.corrupted_metrics,
        settings.paths.corrupted_answers,
    )
    corrupted_quality = run_data_quality_checks(corrupted_df, settings, "corrupted_quality")
    corrupted_freshness_path = settings.paths.quality_dir / "corrupted_freshness.json"
    corrupted_freshness = build_freshness_report(
        corrupted_df, settings, corrupted_freshness_path
    )

    from ingestion.corruption import repair_corrupted_dataframe
    repaired_df = repair_corrupted_dataframe(corrupted_df)
    
    write_csv(repaired_df, settings.paths.repaired_clean_csv)
    write_json(settings.paths.repaired_clean_json, repaired_df.to_dict(orient="records"))
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df, settings, settings.paths.repaired_embeddings_json
    )
    repaired_bundle = evaluate_pipeline(
        settings,
        repaired_index,
        settings.paths.eval_testset,
        settings.paths.repaired_metrics,
        settings.paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(repaired_df, settings, "repaired_quality")
    repaired_freshness_path = settings.paths.quality_dir / "repaired_freshness.json"
    repaired_freshness = build_freshness_report(
        repaired_df, settings, repaired_freshness_path
    )

    current_hash = sha256_file(settings.paths.eval_testset)
    state_hashes = {
        baseline_metrics.get("test_set_sha256"),
        corrupted_bundle.summary.get("test_set_sha256"),
        repaired_bundle.summary.get("test_set_sha256"),
        frozen_hash,
        current_hash,
    }
    if len(state_hashes) != 1:
        raise RuntimeError("The evaluation set changed between baseline, corrupted, and repaired states.")

    generate_corruption_report(
        settings.paths.comparison_report,
        baseline_metrics,
        corrupted_bundle.summary,
        repaired_bundle.summary,
        corrupted_quality,
        repaired_quality,
        corrupted_freshness,
        repaired_freshness,
    )
    generate_metrics_svg(
        settings.paths.project_dir / "data" / "reports" / "metrics_comparison.svg",
        baseline_metrics,
        corrupted_bundle.summary,
        repaired_bundle.summary,
    )
    comparison = {
        "status": "success",
        "test_set_sha256": frozen_hash,
        "baseline": baseline_metrics,
        "corrupted": corrupted_bundle.summary,
        "repaired": repaired_bundle.summary,
        "quality": {"corrupted": corrupted_quality, "repaired": repaired_quality},
        "freshness": {"corrupted": corrupted_freshness, "repaired": repaired_freshness},
        "repair_matches_baseline": False,
    }
    write_json(settings.paths.project_dir / "data" / "results" / "comparison_metrics.json", comparison)
    return comparison


def main() -> None:
    result = run_corruption_pipeline()
    print(
        "Corruption flow completed: "
        f"baseline_hit={result['baseline']['retrieval_hit_rate']:.4f}, "
        f"corrupted_hit={result['corrupted']['retrieval_hit_rate']:.4f}, "
        f"repaired_hit={result['repaired']['retrieval_hit_rate']:.4f}"
    )


if __name__ == "__main__":
    main()
