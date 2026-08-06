"""Custom styling and CSS injector for Streamlit App."""

import streamlit as st

CUSTOM_CSS = """
<style>
    /* Google Fonts Import */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Global Typography & Colors */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Glassmorphism Background Container */
    .stAppViewContainer {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        background-attachment: fixed;
    }

    /* Main Container Padding */
    .main .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        max-width: 1300px;
    }

    /* Header Banner Styling */
    .header-container {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(0, 0, 0, 0.1);
        border-radius: 16px;
        padding: 24px 32px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.1);
    }
    .header-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #2563eb 0%, #7c3aed 50%, #db2777 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.5px;
    }
    .header-subtitle {
        color: #475569;
        font-size: 1.05rem;
        margin-top: 6px;
        margin-bottom: 0;
    }

    /* Metric Cards Styling */
    .metric-card {
        background: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 24px -8px rgba(99, 102, 241, 0.15);
        border-color: rgba(99, 102, 241, 0.3);
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #475569;
        margin-bottom: 8px;
    }
    .metric-val {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0f172a;
        margin-bottom: 4px;
    }
    .metric-sub {
        font-size: 0.8rem;
        font-weight: 500;
    }
    .text-success { color: #059669; }
    .text-danger { color: #dc2626; }
    .text-info { color: #2563eb; }

    /* Custom Status Badges */
    .badge-pass {
        background: rgba(16, 185, 129, 0.15);
        color: #059669;
        border: 1px solid rgba(52, 211, 153, 0.4);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
    }
    .badge-fail {
        background: rgba(244, 63, 94, 0.15);
        color: #e11d48;
        border: 1px solid rgba(248, 113, 113, 0.4);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
    }
    .badge-info {
        background: rgba(99, 102, 241, 0.15);
        color: #4f46e5;
        border: 1px solid rgba(129, 140, 248, 0.4);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        display: inline-block;
    }

    /* Index Switcher Pill Styling */
    .index-pill {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 24px;
        font-weight: 600;
        font-size: 0.9rem;
        margin-right: 8px;
    }
    .index-baseline { background: rgba(52, 211, 153, 0.2); color: #059669; border: 1px solid #34d399; }
    .index-corrupted { background: rgba(248, 113, 113, 0.2); color: #e11d48; border: 1px solid #f87171; }
    .index-repaired { background: rgba(96, 165, 250, 0.2); color: #2563eb; border: 1px solid #60a5fa; }

    /* Streamlit Tabs Custom Glow */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(241, 245, 249, 0.8);
        padding: 8px;
        border-radius: 12px;
        border: 1px solid rgba(0, 0, 0, 0.05);
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        border-radius: 8px;
        color: #475569;
        font-weight: 600;
        font-size: 0.95rem;
        padding: 0 18px;
        border: none !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%) !important;
        color: #0f172a !important;
        border: 1px solid rgba(167, 139, 250, 0.3) !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.05);
    }

    /* Context Document Card */
    .doc-card {
        background: rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-left: 4px solid #4f46e5;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .doc-title {
        font-weight: 700;
        color: #0f172a;
        font-size: 0.95rem;
        margin-bottom: 4px;
    }
    .doc-meta {
        font-size: 0.8rem;
        color: #64748b;
        font-family: 'JetBrains Mono', monospace;
        margin-bottom: 8px;
    }
    .doc-snippet {
        font-size: 0.85rem;
        color: #334155;
        line-height: 1.5;
    }

    /* Code block dark style */
    pre, code {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: rgba(248, 250, 252, 0.95);
        border-right: 1px solid rgba(0, 0, 0, 0.05);
    }
</style>
"""


def apply_custom_styles():
    """Inject custom CSS rules into Streamlit head."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
