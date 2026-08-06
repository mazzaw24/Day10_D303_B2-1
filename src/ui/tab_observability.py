"""Tab 3: Data Observability & Quality Audit Dashboard."""

import pandas as pd
import streamlit as st

from core.config import Settings
from core.utils import read_json


def render_tab_observability():
    """Render Tab 3: Data Observability & Quality Audit."""
    st.markdown("### 🔍 Data Observability & Quality Audit")
    st.markdown(
        "Hệ thống kiểm tra chất lượng dữ liệu tự động (Data Quality Rules & Freshness Monitors) "
        "đóng vai trò là lá chắn phát hiện dị thường trước khi dữ liệu được nạp vào Vector Database."
    )

    settings = Settings.load()

    # Load Quality & Freshness reports
    corrupted_q_path = settings.paths.quality_dir / "corrupted_quality.json"
    repaired_q_path = settings.paths.quality_dir / "repaired_quality.json"
    corr_log_path = settings.paths.results_dir / "corruption_log.json"

    cq_data = read_json(corrupted_q_path) if corrupted_q_path.exists() else {}
    rq_data = read_json(repaired_q_path) if repaired_q_path.exists() else {}

    st.markdown("---")

    # Overall Audit Status Cards
    with st.container():
        c_passed = cq_data.get("passed_checks", 0)
        c_total = len(cq_data.get("checks", []))
        c_status_badge = '<span class="badge-fail">🔴 FAIL (Data Corrupted)</span>' if not cq_data.get("success", False) else '<span class="badge-pass">🟢 PASS</span>'
        st.markdown(
            f"""
            <div class="metric-card" style="border-left: 4px solid #f87171;">
                <div class="metric-label">Corrupted State Data Audit</div>
                <div class="metric-val text-danger">{c_passed} / {c_total} Passed</div>
                <div style="margin-top: 8px;">{c_status_badge}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### 📋 Data Quality Rule Breakdown")

    # Combine Quality Checks into comparison DataFrame
    c_checks = {check["name"]: check for check in cq_data.get("checks", [])}
    r_checks = {check["name"]: check for check in rq_data.get("checks", [])}

    all_rule_names = list(set(list(c_checks.keys()) + list(r_checks.keys())))

    table_rows = []
    for name in sorted(all_rule_names):
        c_item = c_checks.get(name, {})
        r_item = r_checks.get(name, {})

        dimension = c_item.get("dimension") or r_item.get("dimension") or "N/A"
        expectation = c_item.get("expectation") or r_item.get("expectation") or "N/A"

        c_pass = c_item.get("passed", False)
        r_pass = r_item.get("passed", False)

        table_rows.append({
            "Quality Rule": name,
            "Dimension": dimension.capitalize(),
            "Expectation": expectation,
            "Corrupted Observed": c_item.get("observed", "N/A"),
            "Corrupted Status": "🔴 FAIL" if not c_pass else "🟢 PASS",
        })

    df_quality = pd.DataFrame(table_rows)
    st.dataframe(df_quality, width="stretch", hide_index=True)

    st.markdown("---")

    # Freshness & Corruption Logs Sections
    col_fresh, col_logs = st.columns([1, 1])

    with col_fresh:
        st.markdown("### 🕒 Data Freshness Audit")
        f_corr_path = settings.paths.quality_dir / "corrupted_freshness.json"
        f_rep_path = settings.paths.quality_dir / "repaired_freshness.json"

        fc_data = read_json(f_corr_path) if f_corr_path.exists() else {}
        fr_data = read_json(f_rep_path) if f_rep_path.exists() else {}

        st.markdown(
            f"""
            <div style="background: rgba(30, 41, 59, 0.6); padding: 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08);">
                <p><b>Threshold:</b> Within {fc_data.get('freshness_threshold_days', 180)} days of reference date</p>
                <div style="margin-bottom: 12px;">
                    <span style="font-weight: 600; color: #f87171;">🔴 Corrupted State:</span>
                    <ul>
                        <li><b>Stale Rows:</b> {fc_data.get('stale_rows', 0)} / {fc_data.get('total_rows', 0)} ({fc_data.get('stale_ratio', 0)*100:.1f}%)</li>
                        <li><b>Status:</b> <span class="badge-fail">{fc_data.get('status', 'stale').upper()}</span></li>
                    </ul>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_logs:
        st.markdown("### ⚡ Corruption Events Log")
        if corr_log_path.exists():
            c_logs = read_json(corr_log_path)
            st.json(c_logs, expanded=True)
        else:
            st.info("Corruption log file not found.")
