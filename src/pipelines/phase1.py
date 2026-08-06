from __future__ import annotations

from typing import Any

from core.config import Settings, load_settings, require_llm_credentials
from core.utils import now_utc, read_json, sha256_file, write_csv, write_json
from evaluation.metrics import evaluate_pipeline
from evaluation.testset import build_test_set
from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_phase1_report
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question


def _load_or_fetch_records(settings: Settings):
    if settings.paths.raw_records_json.exists() and not settings.refresh_source:
        return load_raw_records(settings.paths.raw_records_json)
    return fetch_source_records(settings)


def run_pipeline(settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or load_settings()
    require_llm_credentials(settings)
    records = _load_or_fetch_records(settings)
    clean_df = build_clean_dataframe(records, now_utc())
    write_csv(clean_df, settings.paths.clean_csv)
    write_json(settings.paths.clean_json, clean_df.to_dict(orient="records"))

    index = LocalEmbeddingIndex.build(clean_df, settings, settings.paths.embeddings_json)
    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        build_test_set(clean_df, settings.paths.eval_testset)
    else:
        test_set = read_json(settings.paths.eval_testset)
        valid_ids = set(clean_df["paper_id"])
        referenced = {doc_id for item in test_set for doc_id in item.get("ground_truth_doc_ids", [])}
        if not referenced or not referenced <= valid_ids:
            raise RuntimeError("Existing frozen evaluation set is incompatible with the current baseline dataset.")

    bundle = evaluate_pipeline(
        settings,
        index,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
        settings.paths.baseline_answers,
    )
    quality = run_data_quality_checks(clean_df, settings, "baseline_quality")
    freshness = build_freshness_report(clean_df, settings, settings.paths.freshness_report)

    raw_payload = read_json(settings.paths.raw_api_response) if settings.paths.raw_api_response.exists() else {}
    acquisition = raw_payload.get("acquisition", {}) if isinstance(raw_payload, dict) else {}
    source_summary = {
        "mode": acquisition.get("mode", "raw_snapshot"),
        "records": len(records),
        "query": acquisition.get("query", settings.source_query),
        "filter": acquisition.get("filter", settings.source_filter),
        "raw_api_response": str(settings.paths.raw_api_response.relative_to(settings.paths.project_dir)),
        "raw_records": str(settings.paths.raw_records_json.relative_to(settings.paths.project_dir)),
    }
    generate_phase1_report(settings.paths.baseline_report, source_summary, bundle.summary, quality, freshness)

    demo = []
    for item in bundle.answers[:4]:
        demo.append(
            {
                "question": item["question"],
                "answer": item["answer"],
                "retrieved_doc_ids": item["retrieved_doc_ids"],
            }
        )
    write_json(settings.paths.demo_answers, demo)

    return {
        "status": "success",
        "records": len(records),
        "clean_rows": len(clean_df),
        "test_set_sha256": sha256_file(settings.paths.eval_testset),
        "metrics": bundle.summary,
        "quality": quality,
        "freshness": freshness,
        "source": source_summary,
    }


def main() -> None:
    result = run_pipeline()
    metrics = result["metrics"]
    print(
        "Baseline pipeline completed: "
        f"rows={result['clean_rows']}, questions={metrics['samples']}, "
        f"retrieval_hit_rate={metrics['retrieval_hit_rate']:.4f}, "
        f"mean_token_f1={metrics['mean_token_f1']:.4f}"
    )


if __name__ == "__main__":
    main()
