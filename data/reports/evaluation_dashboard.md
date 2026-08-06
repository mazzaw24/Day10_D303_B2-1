# Bảng điều khiển Đánh giá (Evaluation Dashboard)

## Tổng quan các chỉ số qua các giai đoạn Pipeline

| Danh mục | Chỉ số | Tiêu chuẩn (Baseline) | Làm nhiễu (Corrupted) | Phục hồi (Repaired) |
|----------|--------|----------|-----------|----------|
| Chất lượng Truy xuất (Retrieval Quality) | Tỷ lệ Hit (Hit Rate) | 100.0% | 33.3% | 16.7% |
| Chất lượng Truy xuất (Retrieval Quality) | Hit@3 | 100.0% | 33.3% | 16.7% |
| Chất lượng Truy xuất (Retrieval Quality) | Hit@5 | 100.0% | 33.3% | 16.7% |
| Chất lượng Truy xuất (Retrieval Quality) | Độ chuẩn xác Ngữ cảnh (Context Precision) | 94.8% | 35.2% | 31.8% |
| Chất lượng Truy xuất (Retrieval Quality) | Độ phủ Ngữ cảnh (Context Recall) | 100.0% | 45.8% | 37.5% |
| Chất lượng Câu trả lời (Answer Quality) | Độ chuẩn xác Token (Token Precision) | 4.9% | 2.9% | 2.9% |
| Chất lượng Câu trả lời (Answer Quality) | Độ phủ Token (Token Recall) | 16.6% | 4.0% | 4.0% |
| Chất lượng Câu trả lời (Answer Quality) | Token F1 | 7.1% | 2.0% | 2.0% |
| Chất lượng Câu trả lời (Answer Quality) | Độ chính xác Giám khảo (Judge Accuracy) | 87.5% | 16.7% | 8.3% |
| Chất lượng Câu trả lời (Answer Quality) | Điểm Giám khảo (Judge Score 1-5) | 4.71 | 1.79 | 1.42 |
| Chất lượng Câu trả lời (Answer Quality) | Tỷ lệ Ảo giác (Hallucination Rate) | 2.1% | 75.0% | 89.6% |
| Hiệu năng (Performance) | Độ trễ trung bình (Avg Latency) | 1.37 | 1.08 | 1.03 |

## So sánh & Biến động

| Chỉ số | Tiêu chuẩn → Làm nhiễu | Làm nhiễu → Phục hồi |
|--------|----------------------|----------------------|
| Tỷ lệ Hit (Hit Rate) | -66.7% | -50.0% |
| Hit@3 | -66.7% | -50.0% |
| Hit@5 | -66.7% | -50.0% |
| Độ chuẩn xác Ngữ cảnh (Context Precision) | -62.9% | -9.5% |
| Độ phủ Ngữ cảnh (Context Recall) | -54.2% | -18.2% |
| Độ chuẩn xác Token (Token Precision) | -41.3% | +0.4% |
| Độ phủ Token (Token Recall) | -75.8% | 0.0% |
| Token F1 | -71.8% | +0.7% |
| Độ chính xác Giám khảo (Judge Accuracy) | -81.0% | -50.0% |
| Điểm Giám khảo (Judge Score 1-5) | -61.9% | -20.9% |
| Tỷ lệ Ảo giác (Hallucination Rate) | +3500.0% | +19.4% |
| Độ trễ trung bình (Avg Latency) | -21.4% | -4.5% |

## Phân tích tự động bằng LLM

# Phân Tích Thay Đổi Chỉ Số Trong Data Observability Pipeline

## Tổng Quan
Trong quá trình quan sát dữ liệu, chúng ta đã theo dõi ba giai đoạn: Tiêu chuẩn (Baseline), Làm nhiễu (Corrupted), và Phục hồi (Repaired). Dưới đây là phân tích chi tiết về các chỉ số và sự thay đổi của chúng.

## Các Chỉ Số Thay Đổi Đáng Kể

### 1. Tỷ lệ Hit (Hit Rate)
- **Baseline**: 100.0%
- **Corrupted**: 33.3% (-66.7%)
- **Repaired**: 16.7% (-50.0%)

**Giải thích**: Tỷ lệ Hit giảm mạnh trong giai đoạn Làm nhiễu do dữ liệu bị làm hỏng, dẫn đến khả năng truy cập và xử lý thông tin giảm sút. Giai đoạn Phục hồi không cải thiện đáng kể, cho thấy các biện pháp phục hồi chưa đủ hiệu quả.

### 2. Độ chuẩn xác Ngữ cảnh (Context Precision)
- **Baseline**: 94.8%
- **Corrupted**: 35.2% (-62.9%)
- **Repaired**: 31.8% (-9.5%)

**Giải thích**: Độ chuẩn xác ngữ cảnh giảm mạnh trong giai đoạn Làm nhiễu, cho thấy dữ liệu không còn chính xác và đáng tin cậy. Giai đoạn Phục hồi chỉ cải thiện nhẹ, cho thấy việc phục hồi không khôi phục được độ chính xác như mong đợi.

### 3. Tỷ lệ Ảo giác (Hallucination Rate)
- **Baseline**: 2.1%
- **Corrupted**: 75.0% (+3500.0%)
- **Repaired**: 89.6% (+19.4%)

**Giải thích**: Tỷ lệ Ảo giác tăng vọt trong giai đoạn Làm nhiễu, cho thấy dữ liệu không chính xác dẫn đến những kết quả sai lệch. Giai đoạn Phục hồi không chỉ không giảm tỷ lệ này mà còn tăng lên, cho thấy các biện pháp phục hồi có thể đã không giải quyết được vấn đề cốt lõi.

### 4. Độ chính xác Giám khảo (Judge Accuracy)
- **Baseline**: 87.5%
- **Corrupted**: 16.7% (-81.0%)
- **Repaired**: 8.3% (-50.0%)

**Giải thích**: Giảm mạnh trong độ chính xác giám khảo cho thấy sự suy giảm nghiêm trọng trong khả năng đánh giá chất lượng dữ liệu. Giai đoạn Phục hồi không cải thiện đáng kể, cho thấy sự cần thiết phải xem xét lại quy trình phục hồi.

## Nguyên Nhân Gây Ra Sự Suy Giảm Trong Giai Đoạn Làm Nhiễu
- **Chất lượng dữ liệu**: Dữ liệu có thể bị lỗi, không chính xác hoặc không đầy đủ.
- **Quá trình xử lý**: Các thuật toán hoặc quy trình xử lý dữ liệu có thể không đủ mạnh để xử lý các tình huống bất thường.
- **Thiếu kiểm soát**: Thiếu các biện pháp kiểm soát chất lượng dữ liệu trong quá trình thu thập và xử lý.

## Mức Độ Hiệu Quả Của Giai Đoạn Phục Hồi
- Giai đoạn Phục hồi cho thấy một số cải thiện nhưng không đủ để khôi phục các chỉ số về mức độ ban đầu. Điều này cho thấy rằng các biện pháp phục hồi cần được cải thiện và tối ưu hóa để có thể khôi phục được chất lượng dữ liệu và độ chính xác.

## Kết Luận
Các chỉ số trong Data Observability pipeline cho thấy sự suy giảm nghiêm trọng trong giai đoạn Làm nhiễu, và giai đoạn Phục hồi chưa đủ hiệu quả để khôi phục lại chất lượng dữ liệu. Cần có các biện pháp cải thiện quy trình phục hồi và kiểm soát chất lượng dữ liệu để đảm bảo tính chính xác và độ tin cậy của dữ liệu trong tương lai.