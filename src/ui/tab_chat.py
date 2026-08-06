"""Tab 1: Live Interactive RAG & Agent Playground."""

import json
from pathlib import Path
import streamlit as st

from core.config import Settings
from core.utils import read_json
from retrieval.index import LocalEmbeddingIndex
from retrieval.qa import answer_question


@st.cache_resource
def get_cached_index(embeddings_path: str):
    """Cache vector index loading for high performance."""
    settings = Settings.load()
    path = Path(embeddings_path)
    if not path.exists():
        return None
    try:
        return LocalEmbeddingIndex.load(settings, path)
    except Exception as e:
        st.error(f"Error loading index from {embeddings_path}: {e}")
        return None


def get_precomputed_answer(question: str, index_key: str) -> dict | None:
    """Find precomputed answer matching the question in data/results/."""
    file_map = {
        "baseline": "data/results/baseline_answers.json",
        "corrupted": "data/results/corrupted_answers.json",
        "repaired": "data/results/repaired_answers.json",
    }
    path_str = file_map.get(index_key)
    if not path_str or not Path(path_str).exists():
        return None
    try:
        data = read_json(Path(path_str))
        for item in data:
            if item.get("question", "").strip().lower() == question.strip().lower():
                return item
    except Exception:
        pass
    return None


def render_tab_chat():
    """Render Tab 1: Live Interactive RAG & Agent Demo."""
    st.markdown("### 💬 Live RAG & Agent Playground")
    st.markdown(
        "Thử nghiệm đặt câu hỏi trực tiếp để kiểm chứng ảnh hưởng của **Data Corruption** "
        "lên kết quả Vector Retrieval và LLM Response."
    )

    settings = Settings.load()

    # Index Selection bar
    col_idx, col_mode = st.columns([2, 1])

    with col_idx:
        index_choice = st.radio(
            "📍 Chọn Index Dữ Liệu (Dataset State):",
            options=["🟢 Baseline (Dữ liệu Sạch)", "🔴 Corrupted (Dữ liệu Lỗi)"],
            index=0,
            horizontal=True,
        )

    index_key_map = {
        "🟢 Baseline (Dữ liệu Sạch)": ("baseline", settings.paths.embeddings_json),
        "🔴 Corrupted (Dữ liệu Lỗi)": ("corrupted", settings.paths.corrupted_embeddings_json),
    }

    index_key, manifest_path = index_key_map[index_choice]

    with col_mode:
        execution_mode = st.selectbox(
            "⚡ Chế độ chạy (Execution Engine):",
            options=["Auto (Live LLM if Key else Pre-computed)", "Force Pre-computed (Offline Fast)", "Live LLM Call"],
        )

    st.markdown("---")

    # Question Selection & Input
    test_set_path = getattr(settings.paths, "test_set_json", None)
    sample_questions = []
    if test_set_path and test_set_path.exists():
        try:
            test_data = read_json(test_set_path)
            sample_questions = [item["question"] for item in test_data if "question" in item]
        except Exception:
            pass

    col_q1, col_q2 = st.columns([1, 1])

    with col_q1:
        selected_sample = st.selectbox(
            "📋 Chọn câu hỏi mẫu từ Evaluation Test Set (24 questions):",
            options=["-- Chọn câu hỏi mẫu --"] + sample_questions,
        )

    with col_q2:
        custom_question = st.text_input(
            "✍️ Hoặc nhập câu hỏi tùy chỉnh:",
            placeholder="Ví dụ: Who authored 'AI-Enabled Force and Torque Control...'?",
        )

    active_question = ""
    if custom_question.strip():
        active_question = custom_question.strip()
    elif selected_sample != "-- Chọn câu hỏi mẫu --":
        active_question = selected_sample

    top_k = st.slider("🔍 Retrieval Top-K Documents:", min_value=1, max_value=5, value=4)

    run_btn = st.button("🚀 Chạy RAG Retrieval & LLM Generation", type="primary", use_container_width=True)

    if run_btn:
        if not active_question:
            st.warning("Vui lòng chọn hoặc nhập một câu hỏi trước khi chạy.")
            return

        st.markdown(f"#### ❓ Question: `{active_question}`")

        index_obj = get_cached_index(str(manifest_path))

        # Check execution strategy
        has_api_key = bool(settings.llm_api_key)
        should_run_live = False

        if execution_mode == "Live LLM Call":
            should_run_live = True
        elif execution_mode == "Force Pre-computed (Offline Fast)":
            should_run_live = False
        else:  # Auto
            should_run_live = has_api_key and index_obj is not None

        ans_text = ""
        retrieved_docs = []
        is_precomputed_used = False

        if should_run_live and index_obj is not None:
            with st.spinner("🔄 Performing Vector Search & Calling LLM API..."):
                try:
                    result = answer_question(
                        question=active_question,
                        settings=settings,
                        index=index_obj,
                        top_k=top_k,
                    )
                    ans_text = result.answer
                    # Fetch retrieved docs
                    searched = index_obj.search(active_question, top_k=top_k)
                    retrieved_docs = searched
                except Exception as ex:
                    st.error(f"⚠️ Live LLM call failed ({ex}). Falling back to precomputed answer.")
                    should_run_live = False

        if not should_run_live:
            precomputed = get_precomputed_answer(active_question, index_key)
            if precomputed:
                ans_text = precomputed.get("answer", "No answer recorded.")
                retrieved_contexts = precomputed.get("retrieved_contexts", [])
                retrieved_doc_ids = precomputed.get("retrieved_doc_ids", [])
                for doc_id, ctx in zip(retrieved_doc_ids, retrieved_contexts):
                    retrieved_docs.append({
                        "paper_id": doc_id,
                        "title": doc_id,
                        "score": 1.0,
                        "content": ctx,
                    })
                is_precomputed_used = True
            else:
                if index_obj:
                    searched = index_obj.search(active_question, top_k=top_k)
                    retrieved_docs = searched
                    ans_text = f"[Offline mode] Found {len(searched)} relevant docs. (Configure LLM API key in .env for live generation)."
                else:
                    ans_text = "Index file not found and no precomputed answer matches this custom question."

        # Display Answer Box
        badge_style = "badge-pass" if index_key != "corrupted" else "badge-fail"
        badge_label = f"Index: {index_key.upper()}" + (" (Pre-computed)" if is_precomputed_used else " (Live Execution)")

        st.markdown(
            f"""
            <div style="background: rgba(255, 255, 255, 0.8); border: 1px solid rgba(0, 0, 0, 0.1); border-radius: 12px; padding: 20px; margin-top: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h4 style="margin: 0; color: #2563eb;">💡 LLM Response</h4>
                    <span class="{badge_style}">{badge_label}</span>
                </div>
                <div style="font-size: 1.05rem; line-height: 1.6; color: #1e293b; background: rgba(241, 245, 249, 0.8); padding: 16px; border-radius: 8px; border: 1px solid rgba(0,0,0,0.05);">
                    {ans_text}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Display Context & Retrieved Docs
        st.markdown("#### 📚 Retrieved Context Documents")

        if not retrieved_docs:
            st.info("Không tìm thấy tài liệu phù hợp trong Index.")
        else:
            for idx, doc in enumerate(retrieved_docs, start=1):
                paper_id = getattr(doc, "paper_id", doc.get("paper_id", "N/A"))
                title = getattr(doc, "title", doc.get("title", "N/A"))
                score = getattr(doc, "score", doc.get("score", 0.0))
                content = getattr(doc, "content", doc.get("content", ""))

                st.markdown(
                    f"""
                    <div class="doc-card">
                        <div class="doc-title">#{idx}. {title}</div>
                        <div class="doc-meta">DOI/ID: {paper_id} | Similarity Score: {score:.4f}</div>
                        <div class="doc-snippet">{content[:400]}...</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Prompt Inspector
        with st.expander("🔍 Inspect Exact Prompt Sent to LLM"):
            ctx_payload = json.dumps([
                {"paper_id": getattr(d, "paper_id", d.get("paper_id", "")),
                 "title": getattr(d, "title", d.get("title", "")),
                 "content": getattr(d, "content", d.get("content", ""))}
                for d in retrieved_docs
            ], ensure_ascii=False, indent=2)
            st.code(
                f"Answer the question using only the retrieved scholarly context below.\n"
                f"Do not use outside knowledge. If the context does not support an answer,\n"
                f"reply exactly: I don't know from the indexed corpus. Keep the answer concise.\n\n"
                f"Question:\n{active_question}\n\n"
                f"Retrieved scholarly context:\n{ctx_payload}",
                language="markdown"
            )
