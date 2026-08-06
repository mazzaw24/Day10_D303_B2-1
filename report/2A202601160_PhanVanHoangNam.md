# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Phan Văn Hoàng Nam             |
| MSSV               | 2A202601160                     |
| Khóa/Lớp         | K4/D303              |
| Tên nhóm         | B2-1     |
| Vai trò chính    | Data Engineer                 |
| Repository         | https://github.com/mazzaw24/Day10_D303_B2-1 |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Data Ingestion, Data Cleaning, Indexing      | `src/ingestion/crossref.py`, `src/ingestion/cleaning.py`, `src/retrieval/index.py`           | Crossref REST API JSON response          | Vector Index, Cleaned JSON Records | Hoàn thành |
| Xây dựng và tích hợp MiniLM Embedding      | `src/retrieval/embeddings.py`           | Raw Text (Title, Abstract)          | Chunked Text & Vector Embeddings | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Hỗ trợ thiết lập Pipeline Validation | Trương Minh Hoàng / QA | Pipeline có thể tự động dừng khi thiếu key OpenAI hoặc parse lỗi |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Lấy dữ liệu từ Crossref API, làm sạch dữ liệu | `data/raw/crossref_records.json` | 22 bản ghi được làm sạch hoàn toàn | Chạy `python script/run_phase1.py` và kiểm tra file |
| Tạo Vector Index bằng FAISS | `data/vector_store/index.faiss` | Vector index artifacts | Kiểm tra thư mục `data/vector_store/` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Phần việc của tôi tạo ra file `crossref_records.json` chứa 22 bài báo khoa học sạch sẽ, có đầy đủ `title`, `abstract` và `published_date`, là nguyên liệu đầu vào cốt lõi cho toàn bộ quy trình sinh câu trả lời RAG và đánh giá sau đó.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Dữ liệu thô từ Crossref API thường có cấu trúc phức tạp, nhiều trường bị thiếu (như abstract) hoặc sai định dạng ngày tháng. Nếu đưa trực tiếp vào RAG, LLM sẽ sinh ra kết quả sai lệch hoặc báo lỗi. Cần một pipeline chuẩn hóa dữ liệu trước khi đưa vào index.

### Cách triển khai

Tôi đã sử dụng requests để gọi API Crossref với query cố định. Sau đó, tôi viết hàm parsing để trích xuất `title`, `abstract` (loại bỏ các thẻ HTML rác như `<jats:p>`), và chuẩn hóa `published_date`. Cuối cùng, tôi sử dụng model MiniLM để tạo vector embedding cho các đoạn text này và lưu vào FAISS vector store.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | JSON payload từ Crossref REST API           |
| Output                         | Danh sách các dict Python chứa dữ liệu sạch, Vector index |
| Module phụ thuộc             | `requests`, `faiss-cpu`, `sentence-transformers` |
| Module sử dụng output        | `src/retrieval/rag.py` (Generation & Retrieval) |
| Điều kiện lỗi cần xử lý | API timeout, Rate limit, Bài báo không có abstract |

### Cách xác minh

```bash
python script/run_phase1.py
```

- **Kết quả mong đợi:** Pipeline chạy mượt mà, lưu file `crossref_records.json` và tạo index.
- **Kết quả thực tế:** 22 bản ghi được lưu, index được build thành công, pipeline chuyển sang bước Evaluation.
- **Artifact/log:** `data/raw/crossref_records.json`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Crossref API giới hạn số lượng request (rate limit) và thỉnh thoảng phản hồi chậm.
- **Các phương án đã cân nhắc:** (1) Fetch dữ liệu live mỗi lần chạy. (2) Fetch một lần và lưu raw snapshot lại để dùng dần.
- **Phương án đã chọn:** Sử dụng raw snapshot (Cache).
- **Lý do:** Trade-off về reproducibility và độ trễ. Đảm bảo tất cả các lần test evaluation và corruption đều dùng chung một bộ dữ liệu đầu vào gốc, tránh việc data thay đổi giữa chừng làm metrics bị sai lệch.
- **Bằng chứng quyết định phù hợp:** Chế độ `acquisition_mode: live_crossref_api` được ghi nhận trong `phase1_report.md` cùng với SHA-256 test set luôn giữ cố định.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `KeyError: 'abstract'` khi parsing dữ liệu.
- **Lệnh hoặc bước tái hiện:** `python script/run_phase1.py` với bộ dữ liệu mới.
- **Nguyên nhân gốc:** Không phải bài báo nào trên Crossref cũng public trường `abstract`.
- **Cách xử lý:** Bổ sung hàm `.get('abstract', '')` và dùng regex để loại bỏ các thẻ XML/HTML đặc thù của Crossref. Lọc bỏ các bài báo có abstract quá ngắn.
- **Cách xác minh sau khi sửa:** Chạy lại luồng ingestion không còn báo lỗi, file JSON đầu ra hoàn toàn sạch.
- **Điều học được:** Luôn phải phòng thủ (defensive programming) khi làm việc với API bên thứ ba.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
Trả lời: Gọi API -> Lọc các trường cần thiết -> Làm sạch text -> Chunking -> Đưa qua model embedding (MiniLM) để lấy vector -> Đưa vào FAISS.
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
Trả lời: Evaluation set chứa các câu hỏi mẫu và ID bài báo (ground truth). Hệ thống retrieval lấy top-k ID, sau đó đối chiếu với ground truth để tính Hit Rate.
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
Trả lời: Quality check kiểm tra tính toàn vẹn (schema, null, độ dài), trong khi Freshness chỉ quan tâm đến việc dữ liệu có quá cũ (stale) so với ngưỡng (ví dụ 5 năm) hay không.
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
Trả lời: Để đảm bảo tính công bằng (A/B testing). Nếu test set thay đổi, ta không thể biết metrics giảm là do dữ liệu hỏng hay do câu hỏi khó hơn.
5. Repair được xem là thành công dựa trên artifact và metric nào?
Trả lời: Dựa vào `comparison_metrics.json` có `repair_matches_baseline = True` và các chỉ số RAG phục hồi về mức ban đầu.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 1.0000 | 0.3333 | 1.0000 | Hit rate sụt giảm mạnh khi bị drop records |
| `mean_token_f1`      | 0.0719 | 0.0200 | 0.0710 | Giảm khi abstract bị nhiễu (inject noise) |
| `judge_accuracy`     | 0.9167 | 0.1667 | 0.8750 | Phục hồi gần như hoàn toàn sau khi repair |
| `mean_judge_score`   | 4.8333 | 1.7917 | 4.7083 | Corruption phá hủy hoàn toàn chất lượng LLM answer |
| Quality checks         | PASS | FAIL | PASS | Great Expectations bắt được ngay lỗi schema |
| Freshness status       | FRESH | STALE | FRESH | Bắt được ngay lỗi sửa đổi năm xuất bản (stale_published) |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. Data corruption (drop records, stale dates) → quality/freshness signal thay đổi (FAIL, STALE) → agent metric thay đổi (Retrieval Hit Rate giảm từ 1.0 xuống 0.33).
2. Repair action (rebuild từ snapshot) → quality/freshness signal phục hồi (PASS, FRESH) → agent metric phục hồi (Hit rate về lại 1.0).

Corruption nào ảnh hưởng rõ nhất và vì sao?

Lỗi `drop_records` ảnh hưởng nghiêm trọng nhất đến hệ thống RAG vì nó xóa luôn các document chứa câu trả lời. Điều này làm cho Retrieval Hit Rate giảm thẳng đứng (từ 100% xuống 33.3%), dẫn đến Ragas context_recall bằng 0 và LLM không có thông tin để trả lời.

Kết quả nào khác với kỳ vọng ban đầu?

Token F1 của baseline vốn đã khá thấp (0.0719). Tôi kỳ vọng nó phải cao hơn, nhưng hóa ra do LLM sinh ra câu trả lời tự nhiên (dài, nhiều từ nối) trong khi ground truth chỉ là một cụm từ ngắn gọn, dẫn đến F1 đo đếm bằng token bị thấp dù nội dung vẫn đúng (thể hiện qua judge_accuracy cao 0.91).

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Tầm quan trọng của Data Observability: Dữ liệu thô hỏng thì mô hình AI xịn đến mấy cũng vô dụng (Garbage in, Garbage out).
2. Thiết kế Reproducible: Việc cố định một frozen test set bằng SHA-256 là yếu tố quyết định để đo lường chính xác tác động của Data Corruption.
3. Cơ chế Fallback: Cần lưu raw snapshot để có thể Repair (khôi phục) lại vector index một cách nhanh chóng khi dữ liệu gặp sự cố.

### Nếu có thêm thời gian

Tôi sẽ xây dựng cơ chế Incremental Ingestion (chỉ nạp và embed các bài báo mới có sự thay đổi thay vì chạy lại toàn bộ) để tiết kiệm chi phí gọi API và thời gian compute cho model embedding. Đo lường bằng thời gian thực thi của phase 1.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Phan Văn Hoàng Nam
**Ngày xác nhận:** 2026-08-06
