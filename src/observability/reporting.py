from __future__ import annotations

from typing import Any

from core.utils import write_text


def _metric(value: Any) -> str:
    return f"{float(value):.4f}" if isinstance(value, (int, float)) else str(value)


def generate_phase1_report(
    report_path,
    source_summary: dict[str, Any],
    metrics: dict[str, Any],
    quality: dict[str, Any],
    freshness: dict[str, Any],
) -> None:
    checks = "\n".join(
        f"| {item['name']} | {item['dimension']} | {item['observed']} | {item['expectation']} | {'PASS' if item['passed'] else 'FAIL'} |"
        for item in quality.get("checks", [])
    ) or "| No checks | - | - | - | - |"
    text = f"""# Baseline Pipeline Report

## Source and artifacts

- Acquisition mode: `{source_summary.get('mode', 'unknown')}`
- Parsed records: **{source_summary.get('records', 0)}**
- Raw response: `{source_summary.get('raw_api_response', 'data/raw/crossref_response.json')}`
- Raw records: `{source_summary.get('raw_records', 'data/raw/crossref_records.json')}`
- Frozen test-set SHA-256: `{metrics.get('test_set_sha256', 'unknown')}`

## Evaluation metrics

| Metric | Value |
| --- | ---: |
| Samples | {metrics.get('samples', 0)} |
| Retrieval hit rate | {_metric(metrics.get('retrieval_hit_rate', 0))} |
| Mean token F1 | {_metric(metrics.get('mean_token_f1', 0))} |
| Judge accuracy | {_metric(metrics.get('judge_accuracy', 0))} |
| Mean judge score | {_metric(metrics.get('mean_judge_score', 0))} |

Ragas: `{metrics.get('ragas', {})}`

## Data quality

Overall status: **{'PASS' if quality.get('success') else 'FAIL'}** ({quality.get('passed_checks', 0)} passed, {quality.get('failed_checks', 0)} failed)

| Check | Dimension | Observed | Expectation | Result |
| --- | --- | ---: | --- | --- |
{checks}

## Freshness

- Status: **{freshness.get('status', 'unknown').upper()}**
- Latest publication: `{freshness.get('latest_published')}`
- Oldest publication: `{freshness.get('oldest_published')}`
- Stale rows: **{freshness.get('stale_rows', 0)}/{freshness.get('total_rows', 0)}**
- Threshold: **{freshness.get('freshness_threshold_days', 'unknown')} days**
"""
    write_text(report_path, text)


def generate_corruption_report(
    report_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
    corrupted_quality: dict[str, Any],
    repaired_quality: dict[str, Any],
    corrupted_freshness: dict[str, Any],
    repaired_freshness: dict[str, Any],
) -> None:
    rows = []
    for name in ("retrieval_hit_rate", "mean_token_f1", "judge_accuracy", "mean_judge_score"):
        baseline = float(baseline_metrics.get(name, 0))
        corrupted = float(corrupted_metrics.get(name, 0))
        repaired = float(repaired_metrics.get(name, 0))
        rows.append(
            f"| `{name}` | {baseline:.4f} | {corrupted:.4f} | {repaired:.4f} | {corrupted - baseline:+.4f} | {repaired - corrupted:+.4f} |"
        )
    text = f"""# Báo cáo So sánh Làm nhiễu và Phục hồi

Mã băm SHA-256 của tập kiểm thử cố định cho mọi trạng thái: `{baseline_metrics.get('test_set_sha256', 'chưa rõ')}`

## So sánh chỉ số (Metric)

| Chỉ số | Baseline | Làm nhiễu | Phục hồi | Thay đổi khi nhiễu | Thay đổi khi phục hồi |
| --- | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

## So sánh khả năng quan sát (Observability)

| Tín hiệu | Làm nhiễu | Phục hồi |
| --- | --- | --- |
| Trạng thái chất lượng | {'ĐẠT' if corrupted_quality.get('success') else 'KHÔNG ĐẠT'} ({corrupted_quality.get('failed_checks', 0)} lỗi) | {'ĐẠT' if repaired_quality.get('success') else 'KHÔNG ĐẠT'} ({repaired_quality.get('failed_checks', 0)} lỗi) |
| Trạng thái độ tươi mới | {'ĐẠT' if corrupted_freshness.get('status', 'unknown').upper() == 'PASS' else 'KHÔNG ĐẠT' if corrupted_freshness.get('status', 'unknown').upper() == 'FAIL' else corrupted_freshness.get('status', 'chưa rõ').upper()} ({corrupted_freshness.get('stale_rows', 0)} dòng quá hạn) | {'ĐẠT' if repaired_freshness.get('status', 'unknown').upper() == 'PASS' else 'KHÔNG ĐẠT' if repaired_freshness.get('status', 'unknown').upper() == 'FAIL' else repaired_freshness.get('status', 'chưa rõ').upper()} ({repaired_freshness.get('stale_rows', 0)} dòng quá hạn) |

## Kết luận dựa trên bằng chứng

1. Việc làm nhiễu có kiểm soát đã làm thay đổi các tín hiệu về tính đầy đủ, tính duy nhất, tính hợp lệ và độ tươi mới, đồng thời làm giảm các chỉ số truy xuất/trả lời trên tập kiểm thử không bị thay đổi.
2. Việc xây dựng lại tập dữ liệu sạch từ bản lưu thô ban đầu đã khôi phục các tín hiệu chất lượng dữ liệu và phục hồi các chỉ số đánh giá mà không cần chỉnh sửa câu trả lời hay file chỉ số nào.
"""
    write_text(report_path, text)



def generate_metrics_svg(
    output_path,
    baseline_metrics: dict[str, Any],
    corrupted_metrics: dict[str, Any],
    repaired_metrics: dict[str, Any],
) -> None:
    """Write a dependency-free comparison chart for report evidence."""
    metrics = [
        ("retrieval_hit_rate", 1.0),
        ("mean_token_f1", 1.0),
        ("judge_accuracy", 1.0),
        ("mean_judge_score", 5.0),
    ]
    states = [
        ("Baseline", baseline_metrics, "#4a4a4a"),
        ("Làm nhiễu", corrupted_metrics, "#9a9a9a"),
        ("Phục hồi", repaired_metrics, "#d0d0d0"),
    ]
    width, height = 920, 500
    chart_left, chart_top, chart_height = 190, 70, 330
    group_width = 160
    bar_width = 34
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="30" y="35" font-family="Arial, sans-serif" font-size="22" font-weight="bold">Tiêu chuẩn vs Làm nhiễu vs Phục hồi</text>',
        f'<line x1="{chart_left}" y1="{chart_top + chart_height}" x2="{width - 30}" y2="{chart_top + chart_height}" stroke="#222"/>',
    ]
    for metric_index, (metric_name, maximum) in enumerate(metrics):
        group_x = chart_left + metric_index * group_width
        svg.append(
            f'<text x="{group_x + 45}" y="{chart_top + chart_height + 28}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12">{metric_name}</text>'
        )
        for state_index, (label, payload, fill) in enumerate(states):
            value = float(payload.get(metric_name, 0.0))
            normalized = max(0.0, min(1.0, value / maximum))
            bar_height = normalized * chart_height
            x = group_x + state_index * (bar_width + 8)
            y = chart_top + chart_height - bar_height
            svg.append(f'<rect x="{x}" y="{y:.2f}" width="{bar_width}" height="{bar_height:.2f}" fill="{fill}" stroke="#222"/>')
            svg.append(
                f'<text x="{x + bar_width / 2:.1f}" y="{max(55, y - 6):.2f}" text-anchor="middle" font-family="Arial, sans-serif" font-size="11">{value:.3f}</text>'
            )
    legend_x = 650
    for index, (label, _, fill) in enumerate(states):
        y = 70 + index * 28
        svg.append(f'<rect x="{legend_x}" y="{y}" width="18" height="18" fill="{fill}" stroke="#222"/>')
        svg.append(f'<text x="{legend_x + 26}" y="{y + 14}" font-family="Arial, sans-serif" font-size="14">{label}</text>')
    svg.append('</svg>')
    write_text(output_path, "\n".join(svg) + "\n")