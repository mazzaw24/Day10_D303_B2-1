import argparse
import json
import os
import sys
from pathlib import Path

# Add src to python path for core config and llm
sys.path.append(str(Path(__file__).parent.parent / "src"))

from core.config import load_settings
from retrieval.llm import build_llm

def safe_pct(val):
    if val is None or val == "N/A":
        return "N/A"
    try:
        return f"{float(val) * 100:.1f}%"
    except (ValueError, TypeError):
        return "N/A"

def safe_float(val, precision=2):
    if val is None or val == "N/A":
        return "N/A"
    try:
        return f"{float(val):.{precision}f}"
    except (ValueError, TypeError):
        return "N/A"

def calc_diff(base, new):
    if base is None or new is None or base == "N/A" or new == "N/A":
        return "N/A"
    try:
        base_f, new_f = float(base), float(new)
        if base_f == 0.0:
            return "N/A"
        diff = ((new_f - base_f) / base_f) * 100
        sign = "+" if diff > 0 else ""
        return f"{sign}{diff:.1f}%"
    except (ValueError, TypeError, ZeroDivisionError):
        return "N/A"

def generate_dashboard():
    settings = load_settings()
    
    paths = {
        "Baseline": settings.paths.baseline_metrics,
        "Corrupted": settings.paths.corrupted_metrics,
        "Repaired": settings.paths.repaired_metrics,
    }
    
    data = {}
    for stage, path in paths.items():
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data[stage] = json.load(f)
        else:
            data[stage] = {}
            
    metrics = [
        ("Chất lượng Truy xuất (Retrieval Quality)", "Tỷ lệ Hit (Hit Rate)", "retrieval_hit_rate", safe_pct),
        ("Chất lượng Truy xuất (Retrieval Quality)", "Hit@3", "hit_at_3", safe_pct),
        ("Chất lượng Truy xuất (Retrieval Quality)", "Hit@5", "hit_at_5", safe_pct),
        ("Chất lượng Truy xuất (Retrieval Quality)", "Độ chuẩn xác Ngữ cảnh (Context Precision)", "mean_context_precision", safe_pct),
        ("Chất lượng Truy xuất (Retrieval Quality)", "Độ phủ Ngữ cảnh (Context Recall)", "mean_context_recall", safe_pct),
        ("Chất lượng Câu trả lời (Answer Quality)", "Độ chuẩn xác Token (Token Precision)", "mean_token_precision", safe_pct),
        ("Chất lượng Câu trả lời (Answer Quality)", "Độ phủ Token (Token Recall)", "mean_token_recall", safe_pct),
        ("Chất lượng Câu trả lời (Answer Quality)", "Token F1", "mean_token_f1", safe_pct),
        ("Chất lượng Câu trả lời (Answer Quality)", "Độ chính xác Giám khảo (Judge Accuracy)", "judge_accuracy", safe_pct),
        ("Chất lượng Câu trả lời (Answer Quality)", "Điểm Giám khảo (Judge Score 1-5)", "mean_judge_score", safe_float),
        ("Chất lượng Câu trả lời (Answer Quality)", "Tỷ lệ Ảo giác (Hallucination Rate)", "mean_hallucination_rate", safe_pct),
        ("Hiệu năng (Performance)", "Độ trễ trung bình (Avg Latency)", "mean_latency_seconds", safe_float),
    ]
    
    # 1. Generate Summary Table
    md_lines = []
    md_lines.append("# Bảng điều khiển Đánh giá (Evaluation Dashboard)\n")
    md_lines.append("## Tổng quan các chỉ số qua các giai đoạn Pipeline\n")
    md_lines.append("| Danh mục | Chỉ số | Tiêu chuẩn (Baseline) | Làm nhiễu (Corrupted) | Phục hồi (Repaired) |")
    md_lines.append("|----------|--------|----------|-----------|----------|")
    
    raw_table_data = []
    
    for category, name, key, fmt in metrics:
        b_val = data.get("Baseline", {}).get(key, "N/A")
        c_val = data.get("Corrupted", {}).get(key, "N/A")
        r_val = data.get("Repaired", {}).get(key, "N/A")
        
        md_lines.append(f"| {category} | {name} | {fmt(b_val)} | {fmt(c_val)} | {fmt(r_val)} |")
        raw_table_data.append((category, name, b_val, c_val, r_val, fmt))

    md_lines.append("\n## So sánh & Biến động\n")
    md_lines.append("| Chỉ số | Tiêu chuẩn → Làm nhiễu | Làm nhiễu → Phục hồi |")
    md_lines.append("|--------|----------------------|----------------------|")
    
    analysis_prompt_lines = ["Hãy phân tích những thay đổi về chỉ số trong một Data Observability pipeline (Tiêu chuẩn -> Làm nhiễu -> Phục hồi):"]
    
    for category, name, b_val, c_val, r_val, fmt in raw_table_data:
        diff_bc = calc_diff(b_val, c_val)
        diff_cr = calc_diff(c_val, r_val)
        md_lines.append(f"| {name} | {diff_bc} | {diff_cr} |")
        
        analysis_prompt_lines.append(f"- {name}: Baseline: {fmt(b_val)} | Corrupted: {fmt(c_val)} ({diff_bc}) | Repaired: {fmt(r_val)} ({diff_cr})")

    # Call LLM for analysis
    md_lines.append("\n## Phân tích tự động bằng LLM\n")
    try:
        llm = build_llm(settings, temperature=0.2)
        prompt = "\n".join(analysis_prompt_lines) + "\n\nGiải thích những chỉ số nào thay đổi đáng kể, nguyên nhân nào có thể gây ra sự suy giảm trong giai đoạn Làm nhiễu (Corrupted phase), và mức độ hiệu quả của giai đoạn Phục hồi (Repair phase). Yêu cầu viết giải thích bằng tiếng Việt, định dạng Markdown, súc tích và tập trung vào các hiểu biết về data observability."
        print("Đang tạo phân tích LLM...")
        response = llm.invoke(prompt)
        analysis_text = getattr(response, "content", str(response))
        md_lines.append(analysis_text)
    except Exception as e:
        md_lines.append(f"*Không thể tạo phân tích LLM: {e}*")

    output_path = settings.paths.project_dir / "data" / "reports" / "evaluation_dashboard.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
        
    print(f"Evaluation dashboard successfully written to {output_path}")

if __name__ == "__main__":
    generate_dashboard()
