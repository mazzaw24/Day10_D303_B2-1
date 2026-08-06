"""Tab: Data Pipeline Explorer."""

import pandas as pd
import streamlit as st

from core.config import Settings
from core.utils import read_json


def render_tab_pipeline():
    """Render Tab: Data Pipeline Explorer."""
    st.markdown("### 🗂️ Data Pipeline Explorer")
    st.markdown(
        "Theo dõi toàn bộ vòng đời của dữ liệu: từ lúc thu thập nguyên bản (Raw), "
        "đến khi phát hiện lỗi & tự động sửa chữa (Cleaned & Repaired), và cuối cùng là "
        "được cắt nhỏ (Chunking) để nạp vào Vector Database."
    )

    settings = Settings.load()

    # Create Sub-tabs for the pipeline stages
    stage1, stage2, stage3 = st.tabs([
        "📄 1. Raw Data", 
        "🧹 2. Cleaned & Corrupted", 
        "🧩 3. Vector Embeddings"
    ])

    with stage1:
        st.markdown("#### Khám phá Dữ liệu Gốc (Raw JSON)")
        st.markdown("Dữ liệu được tải trực tiếp từ Crossref REST API. Thường chứa rất nhiều trường dư thừa, cấu trúc phức tạp và có thể thiếu sót thông tin.")
        
        raw_path = settings.paths.raw_records_json
        if raw_path.exists():
            raw_data = read_json(raw_path)
            st.info(f"Tổng số bản ghi: **{len(raw_data)}**")
            
            # Show a sample of the JSON
            st.markdown("**Dữ liệu mẫu (Sample 1 bản ghi đầu tiên):**")
            if raw_data:
                st.json(raw_data[0], expanded=False)
            
            # Show as dataframe for easier scanning
            st.markdown("**Dạng bảng (Đã được làm phẳng một phần):**")
            try:
                df_raw = pd.DataFrame(raw_data)
                st.dataframe(df_raw.head(15), width="stretch")
            except Exception as e:
                st.error(f"Không thể hiển thị dạng bảng: {e}")
        else:
            st.warning("Không tìm thấy file dữ liệu gốc.")

    with stage2:
        st.markdown("#### So sánh: Dữ liệu đã làm sạch (Cleaned) vs Dữ liệu bị Lỗi (Corrupted)")
        st.markdown(
            "Xem cách hệ thống làm sạch và các dị thường xuất hiện "
            "khi dữ liệu bị làm nhiễu (Corruption)."
        )
        
        with st.expander("ℹ️ Chi tiết các phương pháp làm nhiễu (Corruption Methods)", expanded=False):
            st.markdown(
                """
                Dữ liệu được cố ý làm nhiễu thông qua các phương pháp sau để kiểm thử tính bền vững của RAG và Data Quality checks:
                - **Drop Records:** Loại bỏ ngẫu nhiên một số bản ghi mới nhất.
                - **Blank Summary:** Xóa nội dung tóm tắt (summary) thành chuỗi rỗng.
                - **Inject Noise:** Ghi đè summary bằng một chuỗi nhiễu vô nghĩa (`### CORRUPTED TOKEN STREAM 000 NULL NULL ###`).
                - **Truncate Title:** Cắt cụt tiêu đề bài báo chỉ còn 12 ký tự.
                - **Stale Published Date:** Sửa đổi ngày xuất bản thành một ngày trong quá khứ xa (ví dụ: `2018-01-01`) để tạo ra dữ liệu cũ, lỗi thời.
                - **Duplicate Rows:** Nhân bản một vài bản ghi để tạo dữ liệu trùng lặp.
                """
            )

        cleaned_path = settings.paths.clean_json
        corrupted_path = settings.paths.corrupted_clean_json
        
        if cleaned_path.exists() and corrupted_path.exists():
            df_c = pd.DataFrame(read_json(cleaned_path))
            df_err = pd.DataFrame(read_json(corrupted_path))
            
            comparison_rows = []
            all_ids = df_c['paper_id'].tolist()
            
            c_dict = df_c.set_index('paper_id').to_dict('index')
            e_groups = df_err.groupby('paper_id')
            
            for pid in all_ids:
                c_row = c_dict.get(pid, {})
                e_rows = [row.to_dict() for _, row in e_groups.get_group(pid).iterrows()] if pid in e_groups.groups else []
                
                title_c = str(c_row.get('title', ''))
                display_title = title_c[:45] + '...' if len(title_c) > 45 else title_c
                
                if not e_rows:
                    comparison_rows.append({
                        "paper_id": pid,
                        "Status": "❌ DROPPED",
                        "Original Title": display_title,
                        "Change Highlights": "Bản ghi bị xóa hoàn toàn khỏi tập dữ liệu lỗi"
                    })
                    continue
                    
                if len(e_rows) > 1:
                    comparison_rows.append({
                        "paper_id": pid,
                        "Status": "⚠️ DUPLICATED",
                        "Original Title": display_title,
                        "Change Highlights": f"Bản ghi bị nhân bản thành {len(e_rows)} dòng"
                    })
                    continue
                    
                e_row = e_rows[0]
                is_modified = False
                
                title_e = str(e_row.get('title', ''))
                summary_c = str(c_row.get('summary', ''))
                summary_e = str(e_row.get('summary', ''))
                date_c = str(c_row.get('published', ''))
                date_e = str(e_row.get('published', ''))
                
                details = []
                
                if title_c != title_e:
                    details.append(f"Title ➡️ {title_e}")
                    is_modified = True
                
                if summary_c != summary_e:
                    if summary_e == "":
                        details.append(f"Summary ➡️ [TRỐNG]")
                    else:
                        details.append(f"Summary ➡️ {summary_e[:35]}...")
                    is_modified = True
                    
                if date_c != date_e:
                    details.append(f"Date: {date_c} ➡️ {date_e}")
                    is_modified = True
                    
                if is_modified:
                    comparison_rows.append({
                        "paper_id": pid,
                        "Status": "🔄 MODIFIED",
                        "Original Title": display_title,
                        "Change Highlights": " | ".join(details)
                    })
                else:
                    comparison_rows.append({
                        "paper_id": pid,
                        "Status": "✅ OK",
                        "Original Title": display_title,
                        "Change Highlights": "Giữ nguyên, không có thay đổi"
                    })
                    
            df_comp = pd.DataFrame(comparison_rows)
            # Sắp xếp để các dòng bị thay đổi hiển thị lên trên
            status_order = {"❌ DROPPED": 0, "🔄 MODIFIED": 1, "⚠️ DUPLICATED": 2, "✅ OK": 3}
            df_comp["_order"] = df_comp["Status"].map(status_order)
            df_comp = df_comp.sort_values("_order").drop(columns=["_order"]).reset_index(drop=True)
            
            def color_status(val):
                if "DROPPED" in str(val): return 'color: #f87171; font-weight: bold;'
                if "MODIFIED" in str(val): return 'color: #fbbf24; font-weight: bold;'
                if "DUPLICATED" in str(val): return 'color: #60a5fa; font-weight: bold;'
                return 'color: #34d399;'
                
            st.dataframe(
                df_comp.style.map(color_status, subset=['Status']), 
                width="stretch", 
                height=550,
                hide_index=True
            )
        else:
            st.warning("Không tìm thấy dữ liệu Cleaned hoặc Corrupted.")

    with stage3:
        st.markdown("#### Chunking & Metadata trước khi vào Vector DB")
        st.markdown("Để mô hình LLM có thể tìm kiếm, văn bản dài được chia nhỏ thành các đoạn (chunks) và nhúng (embed) thành vector.")
        
        emb_path = settings.paths.repaired_embeddings_json
        if emb_path.exists():
            emb_data_raw = read_json(emb_path)
            if isinstance(emb_data_raw, dict) and "documents" in emb_data_raw:
                emb_data = emb_data_raw["documents"]
            else:
                emb_data = emb_data_raw

            st.info(f"Tổng số chunks được tạo ra: **{len(emb_data)}**")
            
            if emb_data:
                sample_chunk = emb_data[0]
                
                col_text, col_meta = st.columns([2, 1])
                with col_text:
                    st.markdown("**Nội dung Chunk (Page Content):**")
                    content_text = sample_chunk.get("page_content", sample_chunk.get("content", "N/A"))
                    st.markdown(
                        f"""
                        <div style="background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; font-family: monospace; font-size: 0.9rem; color: #e2e8f0; max-height: 400px; overflow-y: auto;">
                            {content_text}
                        </div>
                        """, unsafe_allow_html=True
                    )
                with col_meta:
                    st.markdown("**Siêu dữ liệu (Metadata):**")
                    st.json(sample_chunk.get("metadata", {}), expanded=True)
                    
            st.markdown("---")
            st.markdown("**Toàn bộ dữ liệu Vector (Dạng bảng - 15 dòng đầu):**")
            df_emb = pd.DataFrame(emb_data)
            if "metadata" in df_emb.columns:
                # Flatten metadata for better tabular view
                meta_df = pd.json_normalize(df_emb["metadata"])
                df_view = pd.concat([df_emb.drop(columns=["metadata"]), meta_df], axis=1)
                df_view = df_view.loc[:, ~df_view.columns.duplicated()]
                st.dataframe(df_view.head(15), width="stretch")
            else:
                st.dataframe(df_emb.head(15), width="stretch")
        else:
            st.warning("Không tìm thấy dữ liệu embeddings.")
