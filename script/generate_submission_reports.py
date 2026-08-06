from __future__ import annotations

from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.utils import read_json, write_text


STRICT_BACKEND = "configured_llm"
RAGAS_KEYS = ("answer_relevancy", "context_precision", "context_recall", "faithfulness")


def _f(value: Any) -> str:
    return f"{float(value):.4f}"


def _read_required(project_root: Path, relative: str) -> Any:
    path = project_root / relative
    if not path.is_file():
        raise RuntimeError(
            f"Missing required artifact: {relative}. Run the strict baseline and corruption pipelines first."
        )
    return read_json(path)


def _validate_strict_metrics(name: str, payload: dict[str, Any]) -> None:
    backends = (
        payload.get("answer_backend"),
        payload.get("judge_backend"),
        payload.get("ragas_backend"),
    )
    if backends != (STRICT_BACKEND, STRICT_BACKEND, STRICT_BACKEND):
        raise RuntimeError(
            f"{name} is not a strict configured-LLM artifact. "
            "Delete legacy metrics and rerun with a valid provider API key."
        )
    ragas = payload.get("ragas")
    if not isinstance(ragas, dict) or any(key not in ragas for key in RAGAS_KEYS):
        raise RuntimeError(
            f"{name} does not contain the four required Ragas metrics from a successful strict run."
        )
    if not payload.get("llm_provider") or not payload.get("llm_model"):
        raise RuntimeError(f"{name} is missing LLM provider/model provenance.")


def _count_tests(project_root: Path) -> int:
    return sum(
        1
        for test_file in (project_root / "tests").glob("test_*.py")
        for line in test_file.read_text(encoding="utf-8").splitlines()
        if line.startswith("def test_")
    )


def _member_rows(team: dict[str, Any]) -> str:
    members = team.get("members") or []
    if not members:
        return "| 1 | Chưa cung cấp | Chưa cung cấp | Chưa cung cấp | Chưa cung cấp |"
    return "\n".join(
        f"| {index} | {member['name']} | {member['student_id']} | {member['role']} | {member['ownership']} |"
        for index, member in enumerate(members, start=1)
    )


def _ragas_rows(baseline: dict, corrupted: dict, repaired: dict) -> str:
    return "\n".join(
        f"| `{key}` | {_f(baseline['ragas'][key])} | {_f(corrupted['ragas'][key])} | {_f(repaired['ragas'][key])} |"
        for key in RAGAS_KEYS
    )


def generate_reports(project_root: Path = ROOT) -> None:
    baseline = _read_required(project_root, "data/results/baseline_metrics.json")
    corrupted = _read_required(project_root, "data/results/corrupted_metrics.json")
    repaired = _read_required(project_root, "data/results/repaired_metrics.json")
    for name, payload in (
        ("baseline_metrics.json", baseline),
        ("corrupted_metrics.json", corrupted),
        ("repaired_metrics.json", repaired),
    ):
        _validate_strict_metrics(name, payload)

    comparison = _read_required(project_root, "data/results/comparison_metrics.json")
    baseline_quality = _read_required(project_root, "data/quality/baseline_quality.json")
    corrupted_quality = _read_required(project_root, "data/quality/corrupted_quality.json")
    repaired_quality = _read_required(project_root, "data/quality/repaired_quality.json")
    baseline_freshness = _read_required(project_root, "data/quality/freshness_report.json")
    corrupted_freshness = _read_required(project_root, "data/quality/corrupted_freshness.json")
    repaired_freshness = _read_required(project_root, "data/quality/repaired_freshness.json")
    corruption_log = _read_required(project_root, "data/results/corruption_log.json")
    raw_payload = _read_required(project_root, "data/raw/crossref_response.json")
    clean_records = _read_required(project_root, "data/clean/papers_clean.json")
    test_set = _read_required(project_root, "data/eval/test_set.json")
    team = _read_required(project_root, "report/team_info.json")

    hashes = {
        baseline.get("test_set_sha256"),
        corrupted.get("test_set_sha256"),
        repaired.get("test_set_sha256"),
        comparison.get("test_set_sha256"),
    }
    if len(hashes) != 1:
        raise RuntimeError("Baseline, corrupted, repaired, and comparison artifacts do not share one frozen test set.")
    provider_models = {
        (baseline.get("llm_provider"), baseline.get("llm_model")),
        (corrupted.get("llm_provider"), corrupted.get("llm_model")),
        (repaired.get("llm_provider"), repaired.get("llm_model")),
    }
    if len(provider_models) != 1:
        raise RuntimeError("All three states must use the same configured LLM provider and model.")

    provider, model = next(iter(provider_models))
    acquisition = raw_payload.get("acquisition", {}) if isinstance(raw_payload, dict) else {}
    test_count = _count_tests(project_root)
    events = corruption_log.get("events") or []
    event_rows = "\n".join(
        f"| {event.get('type', 'unknown')} | {event.get('count', 0)} | {', '.join(event.get('record_ids', [])[:4]) or '-'} |"
        for event in events
    ) or "| Không có | 0 | - |"

    group_report = f"""# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin | Nội dung |
| --- | --- |
| Khóa/Lớp | {team.get('course', 'Chưa cung cấp')} |
| Tên nhóm | {team.get('group_name', 'Chưa cung cấp')} |
| Repository | {team.get('repository', 'Chưa cung cấp')} |
| Ngày hoàn thành | {team.get('completion_date', 'Chưa cung cấp')} |
| Trạng thái metadata nhóm | {team.get('team_metadata_status', 'Chưa cung cấp')} |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò | Module/deliverable sở hữu |
| ---: | --- | --- | --- | --- |
{_member_rows(team)}

## 2. Cấu hình đánh giá bắt buộc

| Thành phần | Cấu hình thực tế |
| --- | --- |
| LLM provider | `{provider}` |
| LLM model | `{model}` |
| Answer generation | configured LLM |
| LLM-as-a-judge | configured LLM |
| Ragas | configured LLM; chạy bắt buộc |
| Frozen test set | `{baseline['test_set_sha256']}` |

Pipeline dừng ngay khi thiếu hoặc sai API key, provider lỗi, model lỗi, LLM trả về lỗi, hoặc Ragas không hoàn thành. Không có cơ chế thay thế kết quả answer/judge/Ragas bằng thuật toán cục bộ.

## 3. Luồng dữ liệu

```text
Crossref REST API hoặc raw snapshot đã lưu
    -> raw artifacts
    -> clean dataset
    -> embedding và index
    -> một frozen evaluation set
    -> configured LLM answer + configured LLM judge + Ragas
    -> baseline evidence
    -> controlled corruption
    -> corrupted evidence
    -> rebuild từ raw snapshot
    -> repaired evidence và comparison
```

- Acquisition mode: `{acquisition.get('mode', 'raw_snapshot')}`.
- Số raw/clean records: **{len(clean_records)}**.
- Số câu hỏi frozen: **{len(test_set)}**.
- Test tự động trong repo: **{test_count} tests**.

## 4. So sánh metrics chính

| Metric | Baseline | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
| Retrieval hit rate | {_f(baseline['retrieval_hit_rate'])} | {_f(corrupted['retrieval_hit_rate'])} | {_f(repaired['retrieval_hit_rate'])} |
| Mean token F1 | {_f(baseline['mean_token_f1'])} | {_f(corrupted['mean_token_f1'])} | {_f(repaired['mean_token_f1'])} |
| Judge accuracy | {_f(baseline['judge_accuracy'])} | {_f(corrupted['judge_accuracy'])} | {_f(repaired['judge_accuracy'])} |
| Mean judge score | {_f(baseline['mean_judge_score'])} | {_f(corrupted['mean_judge_score'])} | {_f(repaired['mean_judge_score'])} |

### Ragas

| Ragas metric | Baseline | Corrupted | Repaired |
| --- | ---: | ---: | ---: |
{_ragas_rows(baseline, corrupted, repaired)}

## 5. Data observability

| Signal | Baseline | Corrupted | Repaired |
| --- | --- | --- | --- |
| Quality | {'PASS' if baseline_quality['success'] else 'FAIL'} | {'PASS' if corrupted_quality['success'] else 'FAIL'} | {'PASS' if repaired_quality['success'] else 'FAIL'} |
| Freshness | {baseline_freshness['status'].upper()} | {corrupted_freshness['status'].upper()} | {repaired_freshness['status'].upper()} |
| Stale rows | {baseline_freshness['stale_rows']} | {corrupted_freshness['stale_rows']} | {repaired_freshness['stale_rows']} |

## 6. Corruption có kiểm soát

| Loại sự cố | Số bản ghi | Ví dụ record ID |
| --- | ---: | --- |
{event_rows}

Mối liên hệ được chứng minh bằng artifacts: **Corruption → quality/freshness signal → retrieval/answer/Ragas impact → repair từ raw snapshot**. `repair_matches_baseline` trong comparison JSON là `{comparison.get('repair_matches_baseline')}`.

## 7. Lệnh tái lập

```bash
python -m pip install -e ".[dev]"
cp .env.example .env
# Điền provider, model và API key thật trong .env
python script/run_phase1.py
python script/run_corruption_flow.py
python script/generate_submission_reports.py
python -m pytest -q
```

## 8. Artifacts đối chiếu

- `data/results/baseline_metrics.json`
- `data/results/corrupted_metrics.json`
- `data/results/repaired_metrics.json`
- `data/results/comparison_metrics.json`
- `data/results/*_answers.json`
- `data/quality/*.json` và `data/quality/gx/*.json`
- `data/reports/phase1_report.md`
- `data/reports/corruption_report.md`
- `data/reports/metrics_comparison.svg`

## 9. Definition of Done

- ✅ Baseline, corruption và repair dùng cùng một frozen test set.
- ✅ Answer generation, LLM judge và Ragas đều dùng provider/model đã cấu hình.
- ✅ Metrics và báo cáo được đọc trực tiếp từ JSON của lần chạy.
- ✅ Repair được dựng lại từ raw snapshot.
- ✅ Không lưu API key trong repo; `.env` bị ignore.
- ⚠️ Bổ sung đúng thông tin và báo cáo cá nhân của các thành viên còn lại trước khi nộp theo nhóm.
"""
    write_text(project_root / "report/group_report.md", group_report)

    individual_template = (project_root / "report/individual_report.md").read_text(encoding="utf-8")
    for member in team.get("members", []):
        text = individual_template
        text = text.replace("[Họ và tên]", member.get("name", "Unknown"))
        text = text.replace("[MSSV]", member.get("student_id", "Unknown"))
        text = text.replace("[K3 hoặc K4]", team.get("course", "Unknown"))
        text = text.replace("[Tên hoặc mã nhóm]", team.get("group_name", "Unknown"))
        text = text.replace("[Vai trò]", member.get("role", "Unknown"))
        text = text.replace("[Đường dẫn repository]", team.get("repository", "Unknown"))
        text = text.replace("[YYYY-MM-DD]", team.get("completion_date", "Unknown"))
        text = text.replace("[Phần việc]", member.get("ownership", "Unknown"), 1)

        text = text.replace(
            "| `retrieval_hit_rate` |      [ ] |       [ ] |      [ ] |",
            f"| `retrieval_hit_rate` | {_f(baseline.get('retrieval_hit_rate'))} | {_f(corrupted.get('retrieval_hit_rate'))} | {_f(repaired.get('retrieval_hit_rate'))} |"
        )
        text = text.replace(
            "| `mean_token_f1`      |      [ ] |       [ ] |      [ ] |",
            f"| `mean_token_f1`      | {_f(baseline.get('mean_token_f1'))} | {_f(corrupted.get('mean_token_f1'))} | {_f(repaired.get('mean_token_f1'))} |"
        )
        text = text.replace(
            "| `judge_accuracy`     |      [ ] |       [ ] |      [ ] |",
            f"| `judge_accuracy`     | {_f(baseline.get('judge_accuracy'))} | {_f(corrupted.get('judge_accuracy'))} | {_f(repaired.get('judge_accuracy'))} |"
        )
        text = text.replace(
            "| `mean_judge_score`   |      [ ] |       [ ] |      [ ] |",
            f"| `mean_judge_score`   | {_f(baseline.get('mean_judge_score'))} | {_f(corrupted.get('mean_judge_score'))} | {_f(repaired.get('mean_judge_score'))} |"
        )
        
        bq = 'PASS' if baseline_quality.get('success') else 'FAIL'
        cq = 'PASS' if corrupted_quality.get('success') else 'FAIL'
        rq = 'PASS' if repaired_quality.get('success') else 'FAIL'
        text = text.replace(
            "| Quality checks         |      [ ] |       [ ] |      [ ] |",
            f"| Quality checks         | {bq} | {cq} | {rq} |"
        )
        
        bf = baseline_freshness.get('status', 'unknown').upper()
        cf = corrupted_freshness.get('status', 'unknown').upper()
        rf = repaired_freshness.get('status', 'unknown').upper()
        text = text.replace(
            "| Freshness status       |      [ ] |       [ ] |      [ ] |",
            f"| Freshness status       | {bf} | {cf} | {rf} |"
        )
        import re, unicodedata
        name_normalized = member.get('name', 'Unknown').replace('Đ', 'D').replace('đ', 'd')
        safe_name = re.sub(r'[^a-zA-Z0-9]', '', ''.join(
            c for c in unicodedata.normalize('NFD', name_normalized)
            if unicodedata.category(c) != 'Mn'
        ))
        filename = f"{member.get('student_id', '0000')}_{safe_name}.md"
        write_text(project_root / f"report/{filename}", text)


if __name__ == "__main__":
    generate_reports(ROOT)
    print("Strict submission reports generated from current API-backed artifacts.")
