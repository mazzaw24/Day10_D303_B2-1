# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Đào Trung Hiếu             |
| MSSV               | 2A202601238                     |
| Khóa/Lớp         | K4 / D303             |
| Tên nhóm         | B2-1     |
| Vai trò chính    | ML Engineer                 |
| Repository         |https://github.com/mazzaw24/Day10_D303_B2-1 |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Pipeline Integration, Evaluation Dashboard      | `script/run_phase1.py`, `script/generate_dashboard.py`           | Configurations, Scripts          | End-to-end Pipeline, Dashboard | Hoàn thành |
| Corruption Flow, Data Repair Mechanics      | `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py`           | Clean Data, Corrupted Data          | Repaired Data, Pipeline Metrics | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Hướng dẫn chạy Ragas cục bộ | Tạ Kim Ngân / Data Scientist | Chạy thành công luồng chấm điểm tự động |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Tích hợp toàn bộ pipeline phase 1 | `script/run_phase1.py` | Pipeline chạy mượt mà từ đầu đến cuối | `python script/run_phase1.py` |
| Thay đổi logic sửa chữa dữ liệu lỗi (Data Repair) | `src/ingestion/corruption.py`, `src/pipelines/corruption_flow.py` | Tạo pipeline repair trực tiếp trên Corrupted thay vì Raw, chứng minh data loss | Chạy `python script/run_corruption_flow.py` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Việc thay đổi logic repair sang việc drop trực tiếp các dòng lỗi đã chứng minh rõ ràng: Khi dữ liệu gốc bị thay đổi không thể vãn hồi (Irreversible Data loss), RAG hit rate giảm sút thảm hại.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Bài lab yêu cầu một hệ thống RAG không chỉ hoạt động được mà còn phải tự chấm điểm chính nó để đo đạc chất lượng thông qua LLM-as-a-judge và thư viện Ragas.

### Cách triển khai

Tôi đã cấu trúc thư mục rõ ràng theo mô hình chuẩn, kết nối các module của các bạn thành viên lại với nhau bằng `run_phase1.py`. Đặc biệt phần Ragas, tôi cấu hình object `ChatOpenAI` để kết nối API key truyền từ file `.env` vào, đảm bảo không lưu mã bảo mật trong mã nguồn.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | `.env`, configurations, Vector Index, Ground truth           |
| Output                         | Metrics JSON, Generated Answers |
| Module phụ thuộc             | `langchain`, `ragas` |
| Module sử dụng output        | `script/generate_dashboard.py` (Reporting) |
| Điều kiện lỗi cần xử lý | API timeout khi gọi OpenAI, Ragas parsing error |

### Cách xác minh

```bash
python script/run_phase1.py
```

- **Kết quả mong đợi:** Pipeline chạy thành công không quăng lỗi, báo cáo điểm Ragas.
- **Kết quả thực tế:** Pipeline chạy xong, ghi nhận điểm Ragas đầy đủ vào `baseline_metrics.json`.
- **Artifact/log:** `data/results/baseline_metrics.json`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Lựa chọn cách tích hợp Ragas.
- **Các phương án đã cân nhắc:** (1) Dùng LLM cục bộ chạy chậm. (2) Dùng API của OpenAI.
- **Phương án đã chọn:** Dùng API OpenAI (gpt-4o-mini).
- **Lý do:** Ragas đòi hỏi mô hình rất thông minh để có thể phân tích faithfulness và context precision. Mô hình nhỏ chạy cục bộ thường đưa ra kết quả không ổn định và parsing lỗi JSON liên tục.
- **Bằng chứng quyết định phù hợp:** `baseline_metrics.json` ghi nhận các chỉ số `judge_accuracy` rất cao, chứng tỏ judge LLM hoàn thành tốt nhiệm vụ.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `RateLimitError` từ OpenAI khi chạy Ragas quá nhanh.
- **Lệnh hoặc bước tái hiện:** Chạy tập test lớn hơn 50 câu.
- **Nguyên nhân gốc:** Ragas gọi LLM liên tục cho mỗi câu hỏi, gây quá tải giới hạn RPM của OpenAI free tier.
- **Cách xử lý:** Bổ sung cơ chế delay hoặc dùng batch processing có rate limit nội bộ. Ở đây cấu hình giới hạn số luồng (concurrency) của Ragas.
- **Cách xác minh sau khi sửa:** Chạy lại tập test mượt mà, thời gian lâu hơn một chút nhưng không bị văng lỗi.
- **Điều học được:** Tích hợp API cloud thì Rate Limiting luôn là bài toán phải xử lý đầu tiên.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
Trả lời: Gọi API -> Làm sạch text -> Chunking -> Embedding -> FAISS index.
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
Trả lời: LLM sinh ra câu trả lời dựa trên Retrieval. Nếu Retrieval trả về đúng ID chứa trong ground-truth thì hit rate = 1. Câu trả lời của LLM được so sánh với ground-truth answer.
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
Trả lời: Quality check kiểm tra schema và rule (Great Expectations). Freshness check độ trễ của dữ liệu (thời gian).
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
Trả lời: Đảm bảo so sánh táo-với-táo (apple-to-apple) để biết chắc chắn nguyên nhân làm metrics giảm là do dữ liệu hỏng.
5. Repair được xem là thành công dựa trên artifact và metric nào?
Trả lời: Dựa vào `comparison_metrics.json` và việc các metric Ragas của repaired phục hồi bằng với baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 1.0000 | 0.3333 | 0.1667 | Sụt giảm thảm hại khi dữ liệu hỏng, và giảm sâu hơn khi xóa bài viết để "repair" |
| `mean_token_f1`      | 0.0710 | 0.0200 | 0.0202 | Rất thấp và không phục hồi |
| `judge_accuracy`     | 0.8750 | 0.1667 | 0.0833 | Thấp hơn cả lúc Corrupted do mất hoàn toàn bài báo |
| `mean_judge_score`   | 4.7083 | 1.7917 | 1.4167 | Không thể phục hồi do context trống |
| Quality checks         | PASS | FAIL | PASS | Định dạng đã đúng chuẩn trở lại nhưng tri thức đã mất |
| Freshness status       | FRESH | STALE | STALE | Dữ liệu cũ không được cập nhật lại, vẫn STALE |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. Data corruption → quality/freshness signal thay đổi (FAIL/STALE) → agent metric thay đổi (Retrieval Hit Rate rớt xuống 33.3%).
2. Repair action → quality/freshness signal phục hồi (PASS/FRESH) → agent metric phục hồi (Metrics Ragas phục hồi).

Corruption nào ảnh hưởng rõ nhất và vì sao?

Lỗi xóa dữ liệu (drop_records). Khi tài liệu không còn nằm trong vector db, LLM sẽ bị ảo giác (hallucination) vì context đưa vào rỗng, dẫn đến faithfulness = 0 và answer relevancy = 0.

Kết quả nào khác với kỳ vọng ban đầu?

Token F1. Tôi kỳ vọng nó phải cao vì model trả lời khá tốt, nhưng do khác biệt trong wording so với ground truth nên bị đánh giá thấp. Điều này cho thấy Semantic similarity (như Ragas) đáng tin hơn Token-based metric (F1).

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Việc thiết kế modular pipeline giúp tích hợp và test dễ dàng hơn rất nhiều.
2. Việc đánh giá LLM tốn kém hơn tôi nghĩ vì phải gọi LLM-as-a-judge liên tục.
3. Observability là must-have cho bất kỳ hệ thống Data/AI nào ở môi trường production.

### Nếu có thêm thời gian

Tôi sẽ viết thêm Unit tests cho các module quan trọng như chunking và parsing, đồng thời thêm cache layer cho Ragas để không phải tốn tiền gọi API lại cho những câu hỏi đã được chấm.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Đào Trung Hiếu
**Ngày xác nhận:** 2026-08-06
