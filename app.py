"""Streamlit Web Application Entrypoint — Day 10 Data Observability & RAG."""

import os
from pathlib import Path
import sys

# Ensure src directory is in Python path
SRC_PATH = Path(__file__).resolve().parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

import dotenv
import streamlit as st

# Page Configuration - Must be the first Streamlit command
st.set_page_config(
    page_title="Day 10: Data Observability & RAG System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load environment variables
dotenv.load_dotenv()

from core.config import Settings
from ui.styles import apply_custom_styles
from ui.tab_lessons import render_tab_lessons
from ui.tab_observability import render_tab_observability
from ui.tab_pipeline import render_tab_pipeline
from ui.tab_results import render_tab_results


def main():
    """Main application loop."""
    # Apply custom Glassmorphic CSS styling
    apply_custom_styles()

    settings = Settings.load()

    # Header Banner
    st.markdown(
        """
        <div class="header-container">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1 class="header-title">🛡️ Data Observability & RAG System</h1>
                    <p class="header-subtitle">
                        Day 10: Trực quan hóa Data Pipeline, Đánh giá Chất lượng Dữ liệu, Auto-Repair & Live RAG Playground
                    </p>
                </div>
                <div style="text-align: right;">
                    <span class="badge-info">Lab 10 — K4</span><br>
                    <span style="font-size: 0.85rem; color: #94a3b8; font-weight: 600;">Student ID: 2A202601238</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sidebar Information & Settings
    with st.sidebar:
        st.markdown("### ⚙️ System Configuration")
        st.markdown(f"**Embedding Model:** `{settings.embedding_model}`")
        st.markdown(f"**Default LLM Provider:** `{settings.llm_provider.upper()}`")
        st.markdown(f"**LLM Model:** `{settings.llm_model}`")

        api_key_status = "🟢 Configured" if settings.llm_api_key else "🔴 Missing (Using Pre-computed fallback)"
        st.markdown(f"**LLM API Key:** {api_key_status}")

        st.markdown("---")
        st.markdown("### 📌 Navigation Quick Overview")
        st.markdown(
            "1. **📊 Results & Metrics**: So sánh Hit Rate, Token F1, LLM Judge Accuracy.\n"
            "2. **🔍 Data Observability**: Kiểm tra Data Quality Rules & Freshness.\n"
            "3. **🗂️ Data Pipeline Explorer**: Trực quan hóa dữ liệu Raw -> Cleaned -> Vector DB.\n"
            "4. **💡 Lessons Learned**: Bài học kinh nghiệm & phân công nhóm."
        )

        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: #64748b; font-size: 0.8rem;'>"
            "Made with ❤️ by Group 1 — Day 10 Data Pipeline"
            "</div>",
            unsafe_allow_html=True,
        )

    # Create Main Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Results & Metrics Evaluation",
        "🔍 Data Observability & Audit",
        "🗂️ Data Pipeline Explorer",
        "💡 Insights & Lessons Learned",
    ])

    with tab1:
        render_tab_results()

    with tab2:
        render_tab_observability()

    with tab3:
        render_tab_pipeline()

    with tab4:
        render_tab_lessons()



if __name__ == "__main__":
    main()
