"""Tab 2: Results & Metrics Evaluation Dashboard."""

from pathlib import Path
import pandas as pd
import streamlit as st

from core.config import Settings
from core.utils import read_json


def render_tab_results():
    """Render Tab 2: Results & Metrics Evaluation."""
    st.markdown("### 📊 Metrics & Performance Comparison")
    st.markdown(
        "Báo cáo và so sánh hiệu năng chi tiết giữa 2 giai đoạn: "
        "🟢 **Baseline** (Gốc), 🔴 **Corrupted** (Bị làm nhiễu dữ liệu)."
    )

    settings = Settings.load()
    metrics_path = settings.paths.results_dir / "comparison_metrics.json"

    if not metrics_path.exists():
        st.error(f"File {metrics_path} không tồn tại. Vui lòng kiểm tra lại data pipeline.")
        return

    data = read_json(metrics_path)
    baseline = data.get("baseline", {})
    corrupted = data.get("corrupted", {})
    repaired = data.get("repaired", {})

    st.markdown("---")

    # 4 Top KPI Metric Cards
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Retrieval Hit Rate</div>
                <div class="metric-val text-danger">{corrupted.get('retrieval_hit_rate', 0)*100:.1f}%</div>
                <div class="metric-sub">
                    Baseline: {baseline.get('retrieval_hit_rate', 0)*100:.1f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Mean Token F1</div>
                <div class="metric-val text-danger">{corrupted.get('mean_token_f1', 0):.4f}</div>
                <div class="metric-sub">
                    Baseline: {baseline.get('mean_token_f1', 0):.4f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">LLM Judge Accuracy</div>
                <div class="metric-val text-danger">{corrupted.get('judge_accuracy', 0)*100:.1f}%</div>
                <div class="metric-sub">
                    Baseline: {baseline.get('judge_accuracy', 0)*100:.1f}%
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi_col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Mean Judge Score</div>
                <div class="metric-val text-danger">{corrupted.get('mean_judge_score', 0):.2f} / 5.0</div>
                <div class="metric-sub">
                    Baseline: {baseline.get('mean_judge_score', 0):.2f}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 📈 Visual Metrics Comparison")

    # Metrics Bar Chart Data
    chart_df = pd.DataFrame([
        {
            "State": "Baseline",
            "Hit Rate (%)": baseline.get("retrieval_hit_rate", 0) * 100,
            "Token F1 (x100)": baseline.get("mean_token_f1", 0) * 100,
            "Judge Accuracy (%)": baseline.get("judge_accuracy", 0) * 100,
            "Judge Score (/5)": baseline.get("mean_judge_score", 0) * 20,
        },
        {
            "State": "Corrupted",
            "Hit Rate (%)": corrupted.get("retrieval_hit_rate", 0) * 100,
            "Token F1 (x100)": corrupted.get("mean_token_f1", 0) * 100,
            "Judge Accuracy (%)": corrupted.get("judge_accuracy", 0) * 100,
            "Judge Score (/5)": corrupted.get("mean_judge_score", 0) * 20,
        },
    ]).set_index("State")

    try:
        import plotly.graph_objects as go

        fig = go.Figure()
        categories = ["Retrieval Hit Rate (%)", "LLM Judge Accuracy (%)", "Mean Judge Score (Scaled %)", "Token F1 (x100)"]
        
        baseline_vals = [
            baseline.get("retrieval_hit_rate", 0) * 100,
            baseline.get("judge_accuracy", 0) * 100,
            (baseline.get("mean_judge_score", 0) / 5.0) * 100,
            baseline.get("mean_token_f1", 0) * 100,
        ]
        corrupted_vals = [
            corrupted.get("retrieval_hit_rate", 0) * 100,
            corrupted.get("judge_accuracy", 0) * 100,
            (corrupted.get("mean_judge_score", 0) / 5.0) * 100,
            corrupted.get("mean_token_f1", 0) * 100,
        ]

        fig.add_trace(go.Bar(x=categories, y=baseline_vals, name="🟢 Baseline", marker_color="#34d399"))
        fig.add_trace(go.Bar(x=categories, y=corrupted_vals, name="🔴 Corrupted", marker_color="#f87171"))

        fig.update_layout(
            barmode="group",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15, 23, 42, 0.6)",
            font=dict(family="Plus Jakarta Sans", color="#f8fafc"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=40, b=20),
            height=380,
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.bar_chart(chart_df)

    st.markdown("---")

    # Detailed Query-level Comparison Table
    st.markdown("### 🔍 Query-Level Answer Comparison Breakdown")
    st.markdown("Chọn một câu hỏi bất kỳ trong 24 câu test set để soi chi tiết câu trả lời của LLM qua 3 giai đoạn:")

    b_answers = read_json(settings.paths.results_dir / "baseline_answers.json") if (settings.paths.results_dir / "baseline_answers.json").exists() else []
    c_answers = read_json(settings.paths.results_dir / "corrupted_answers.json") if (settings.paths.results_dir / "corrupted_answers.json").exists() else []

    questions = [item["question"] for item in b_answers]

    if not questions:
        st.info("Không có dữ liệu answers json để hiển thị.")
        return

    selected_q = st.selectbox("🎯 Chọn câu hỏi để inspect:", questions)

    # Find matching items
    b_item = next((item for item in b_answers if item.get("question") == selected_q), {})
    c_item = next((item for item in c_answers if item.get("question") == selected_q), {})

    st.markdown(f"**Ground Truth (Đáp án chuẩn):** `{b_item.get('ground_truth', 'N/A')}`")

    col_b, col_c = st.columns(2)

    with col_b:
        st.markdown(
            f"""
            <div style="background: rgba(52, 211, 153, 0.1); border: 1px solid rgba(52, 211, 153, 0.3); border-radius: 10px; padding: 16px; min-height: 240px;">
                <h5 style="color: #34d399; margin-top: 0;">🟢 Baseline Answer</h5>
                <p><b>Hit:</b> {b_item.get('retrieval_hit')} | <b>Judge Score:</b> {b_item.get('judge', {}).get('score', 'N/A')}/5</p>
                <div style="font-size: 0.9rem; color: #e2e8f0; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 6px;">
                    {b_item.get('answer', 'N/A')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_c:
        st.markdown(
            f"""
            <div style="background: rgba(248, 113, 113, 0.1); border: 1px solid rgba(248, 113, 113, 0.3); border-radius: 10px; padding: 16px; min-height: 240px;">
                <h5 style="color: #f87171; margin-top: 0;">🔴 Corrupted Answer</h5>
                <p><b>Hit:</b> {c_item.get('retrieval_hit')} | <b>Judge Score:</b> {c_item.get('judge', {}).get('score', 'N/A')}/5</p>
                <div style="font-size: 0.9rem; color: #e2e8f0; background: rgba(0,0,0,0.3); padding: 10px; border-radius: 6px;">
                    {c_item.get('answer', 'N/A')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
