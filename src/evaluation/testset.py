from __future__ import annotations

from typing import Any

import pandas as pd

from core.utils import first_sentence, write_json


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    required = {
        "paper_id",
        "title",
        "summary",
        "authors_joined",
        "categories_joined",
        "published",
    }
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Clean dataframe is missing columns: {sorted(missing)}")
    if len(df) < 4:
        raise ValueError("At least four clean documents are required to build the evaluation set.")

    selected = df.sort_values(["published", "paper_id"], ascending=[False, True]).head(min(6, len(df)))
    samples: list[dict[str, Any]] = []
    for row in selected.to_dict(orient="records"):
        title = row["title"]
        paper_id = row["paper_id"]
        questions = [
            ("summary", f"What is the main finding of '{title}'?", first_sentence(row["summary"])),
            ("authors", f"Who authored '{title}'?", row["authors_joined"]),
            ("date", f"When was '{title}' published?", row["published"]),
            ("categories", f"What categories are assigned to '{title}'?", row["categories_joined"]),
        ]
        for question_type, question, ground_truth in questions:
            samples.append(
                {
                    "id": f"{paper_id}::{question_type}",
                    "question_type": question_type,
                    "question": question,
                    "ground_truth": str(ground_truth),
                    "ground_truth_doc_ids": [paper_id],
                }
            )
    write_json(output_path, samples)
    return samples
