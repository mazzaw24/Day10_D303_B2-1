from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.utils import write_json


def _rebuild_derived(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["summary"] = result["summary"].fillna("").astype(str)
    result["title"] = result["title"].fillna("").astype(str)
    result["summary_chars"] = result["summary"].str.len()
    result["text_for_embedding"] = result.apply(
        lambda row: (
            f"Title: {row['title']}\nAuthors: {row['authors_joined']}\nCategories: {row['categories_joined']}\n"
            f"Published: {row['published']}\nSummary: {row['summary']}"
        )
        if row["summary"] and row["title"]
        else "",
        axis=1,
    )
    return result


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path) -> pd.DataFrame:
    if len(df) < 8:
        raise ValueError("At least eight rows are required for the controlled corruption flow.")
    working = df.sort_values(["published", "paper_id"], ascending=[False, True]).reset_index(drop=True).copy()
    events: list[dict] = []

    drop_count = max(2, min(3, len(working) // 4))
    dropped_ids = working.head(drop_count)["paper_id"].tolist()
    working = working.iloc[drop_count:].reset_index(drop=True)
    events.append({"type": "drop_records", "record_ids": dropped_ids, "count": len(dropped_ids)})

    blank_index = 0
    blank_id = str(working.loc[blank_index, "paper_id"])
    working.loc[blank_index, "summary"] = ""
    events.append({"type": "blank_summary", "record_ids": [blank_id], "count": 1})

    noise_index = min(1, len(working) - 1)
    noise_id = str(working.loc[noise_index, "paper_id"])
    working.loc[noise_index, "summary"] = "### CORRUPTED TOKEN STREAM 000 NULL NULL ###"
    events.append({"type": "inject_noise", "record_ids": [noise_id], "count": 1})

    title_index = min(2, len(working) - 1)
    title_id = str(working.loc[title_index, "paper_id"])
    working.loc[title_index, "title"] = str(working.loc[title_index, "title"])[:12]
    events.append({"type": "truncate_title", "record_ids": [title_id], "count": 1, "max_chars": 12})

    stale_count = min(len(working), max(5, len(working) // 3))
    stale_indexes = list(range(stale_count))
    stale_ids = [str(working.loc[index, "paper_id"]) for index in stale_indexes]
    for index in stale_indexes:
        working.loc[index, "published"] = "2018-01-01"
        working.loc[index, "age_days"] = 3000
    events.append({"type": "stale_published", "record_ids": stale_ids, "count": len(stale_ids), "date": "2018-01-01"})

    duplicate = working.iloc[[min(3, len(working) - 1)]].copy()
    duplicate_ids = duplicate["paper_id"].astype(str).tolist()
    working = pd.concat([working, duplicate], ignore_index=True)
    events.append({"type": "duplicate_rows", "record_ids": duplicate_ids, "count": len(duplicate_ids)})

    working = _rebuild_derived(working)
    payload = {
        "input_rows": int(len(df)),
        "output_rows": int(len(working)),
        "events": events,
        "deterministic": True,
    }
    write_json(Path(output_log_path), payload)
    return working.reset_index(drop=True)

def repair_corrupted_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    working = df.copy()
    
    # 1. Loại bỏ các dòng trùng lặp (duplicate) dựa trên paper_id
    working = working.drop_duplicates(subset=["paper_id"], keep="first")
    
    # 2. Xóa bỏ các dòng không có tóm tắt (blank_summary)
    working = working[working["summary"] != ""]
    
    # 3. Xóa bỏ các dòng bị tiêm nhiễu rác (inject_noise)
    working = working[~working["summary"].str.contains("CORRUPTED TOKEN STREAM", na=False)]
    
    # 4. (Tùy chọn) Không thể khôi phục lại dữ liệu bị drop hoặc title bị truncate 
    # trừ phi gọi lại API, nên ta đành chấp nhận thiếu sót.
    
    return _rebuild_derived(working).reset_index(drop=True)
