"""Tab 4: Insights, Lessons Learned & Team Delegation."""

import streamlit as st


def render_tab_lessons():
    """Render Tab 4: Insights & Lessons Learned."""
    st.markdown("### 💡 Key Takeaways & Lessons Learned")
    st.markdown(
        "Tổng kết các bài học kinh nghiệm cốt lõi rút ra từ thực nghiệm xây dựng "
        "Data Observability Pipeline & RAG System cho bài Lab 10."
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            <div style="background: rgba(30, 41, 59, 0.6); padding: 22px; border-radius: 14px; border-left: 4px solid #6366f1; margin-bottom: 20px;">
                <h4 style="color: #818cf8; margin-top: 0;">1. Nguyên lý "Garbage In, Garbage Out" trong RAG</h4>
                <p style="color: #cbd5e1; line-height: 1.6;">
                    Chất lượng câu trả lời của LLM phụ thuộc 100% vào tính chính xác của dữ liệu được retrieve. 
                    Khi dữ liệu bị nhiễm nhiễu (corrupted):
                </p>
                <ul>
                    <li><b class="text-danger">Retrieval Hit Rate sụt giảm nghiêm trọng từ 100% xuống 33.3%</b>.</li>
                    <li><b class="text-danger">LLM Judge Accuracy giảm từ 91.7% xuống chỉ còn 16.7%</b>.</li>
                </ul>
            </div>
            
            <div style="background: rgba(30, 41, 59, 0.6); padding: 22px; border-radius: 14px; border-left: 4px solid #34d399;">
                <h4 style="color: #34d399; margin-top: 0;">2. Vai trò cốt lõi của Raw Data Snapshot</h4>
                <p style="color: #cbd5e1; line-height: 1.6;">
                    Việc giữ lại <code>raw_snapshot.json</code> (dữ liệu nguyên bản từ Crossref API) 
                    cho phép hệ thống thực hiện <b>Rebuild Pipeline</b> khôi phục lại 100% 
                    dữ liệu sạch ban đầu mà không cần gọi lại API bên ngoài, đảm bảo tính khép kín và nhất quán.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
            <div style="background: rgba(30, 41, 59, 0.6); padding: 22px; border-radius: 14px; border-left: 4px solid #f472b6; margin-bottom: 20px;">
                <h4 style="color: #f472b6; margin-top: 0;">3. Data Observability là "Lá Chắn" Bảo vệ RAG</h4>
                <p style="color: #cbd5e1; line-height: 1.6;">
                    Các bộ quy tắc kiểm tra <b>Data Quality (Completeness, Uniqueness, Validity)</b> 
                    và <b>Data Freshness</b> giúp phát hiện các sự cố dữ liệu (như rỗng summary, lặp ID, dữ liệu lỗi thời) 
                    NGAY TRƯỚC KHI dữ liệu được Index vào Vector Database, ngăn ngừa LLM bị ảo giác (hallucination).
                </p>
            </div>

            <div style="background: rgba(30, 41, 59, 0.6); padding: 22px; border-radius: 14px; border-left: 4px solid #60a5fa;">
                <h4 style="color: #60a5fa; margin-top: 0;">4. Khả năng Mở rộng & Đa mô hình (Multi-Provider Support)</h4>
                <p style="color: #cbd5e1; line-height: 1.6;">
                    Kiến trúc RAG được thiết kế linh hoạt hỗ trợ cả <b>Google Gemini API</b> và <b>OpenAI API</b>, 
                    kèm theo cơ chế fallback thông minh sang Offline Pre-computed Dataset giúp ứng dụng luôn hoạt động ổn định trong mọi điều kiện.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

