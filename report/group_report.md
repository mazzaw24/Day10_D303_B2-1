# Group Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | K4 / D303 |
| Tên nhóm         | B2-1 |
| Repository         |  https://github.com/mazzaw24/Day10_D303_B2-1 |
| Ngày hoàn thành | 2026-08-06 |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | Đào Trung Hiếu | 2A202601238 | ML Engineer | Pipeline Integration, Evaluation Dashboard, Corruption Flow, Data Repair |
| 2 | Phan Văn Hoàng Nam | 2A202601160 | Data Engineer | Data Ingestion, Data Cleaning, Indexing |
| 3 | Trương Minh Hoàng | 2A202601262 | Team Leader / Analyst | Team Coordination, Data Quality Checks, Freshness Constraints |
| 4 | Tạ Kim Ngân | 2A202601258 | Data Scientist | LLM Judge Evaluation, Ragas Integration |
| 5 | Phạm Thế Đăng | 2A202601766 | Documentation/AI Ops | Result Analysis, Reporting, Observability Evidence |

## 2. Tóm tắt kết quả

**Tóm tắt của nhóm:**
Nhóm đã hoàn thành toàn bộ các hạng mục yêu cầu bao gồm: Baseline data pipeline (từ ingestion đến evaluation), báo cáo observability (Data Quality & Freshness), kịch bản corruption, và pipeline repair dữ liệu từ nguồn gốc (raw snapshot).
Baseline pipeline đã tạo ra thành công các artifacts chính: `raw_records.json`, `clean_dataset.csv`, `embeddings_index`, `evaluation_set.json` (24 câu hỏi từ 22 bản ghi) và các reports về metrics, data quality. 
Trong kịch bản giả lập lỗi (corruption), các thao tác làm mất/bẩn dữ liệu (drop_records, stale_published) đã gây ảnh hưởng nặng nề đến pipeline, khiến hệ thống báo STALE và FAIL các rule, kéo theo retrieval hit rate giảm mạnh xuống còn 0.33 và Judge accuracy chỉ còn 0.16. 
Tuy nhiên, quy trình repair từ raw snapshot đã hoạt động đúng đắn, phục hồi thành công chất lượng dữ liệu và đưa các chỉ số retrieval (1.0) cũng như Judge accuracy (~0.875) trở lại gần như nguyên vẹn trạng thái baseline.

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | Crossref API | Fetch data, lưu snapshot   | `data/raw/raw_records.json` | Hoàng Nam |
| Cleaning          | Raw records        | Làm sạch title/summary, xử lý date | `data/clean/clean_dataset.json` | Hoàng Nam |
| Embedding/index   | Clean records  | Embedding qua ChromaDB       | `data/embeddings/` | Hoàng Nam |
| Evaluation        | Index, test set | Chạy QA, tính toán Token F1, LLM Judge | `data/results/baseline_metrics.json` | Kim Ngân |
| Observability     | Clean records  | Kiểm tra tính toàn vẹn và độ tươi mới | `data/quality/*.json` | Minh Hoàng |
| Corruption/repair | Clean/Raw records  | Tạo lỗi giả lập và rebuild data    | `data/results/corrupted_metrics.json` | Trung Hiếu |
| Orchestration     | Scripts  | Điều phối Phase 1, Corruption, Reports | `data/reports/*.md` | Thế Đăng |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | openai |
| `LLM_MODEL`                | gpt-4o-mini |
| Embedding model              | default |
| Số lượng Crossref records | 22 |
| Retrieval`top_k`           | 3 (default) |
| Freshness threshold          | default |

### Lệnh cài đặt

```bash
python -m pip install -e ".[dev]"
```

### Lệnh chạy

Baseline:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
python script/run_corruption_flow.py
python script/generate_submission_reports.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ------------------------------------ |
| Baseline pipeline | Thành công | Phase 1 report, baseline_metrics.json |
| Corruption flow   | Thành công | Corruption report, comparison_metrics.json |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | Crossref REST API (live_crossref_api) |
| Query/filter                | default                  |
| Số record nhận được    | 22                         |
| Cơ chế retry/backoff      | Exponential backoff 4 attempts (code in ingestion/crossref.py) |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| paper_id | string | Có | Mã định danh paper | Bỏ qua bản ghi |
| title | string | Có | Tựa đề paper | Bỏ qua bản ghi |
| summary | string | Có | Tóm tắt (min 40 chars) | Bỏ qua bản ghi |
| published | date/string | Có | Ngày xuất bản | Parse errors -> Bỏ qua bản ghi |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| Bỏ qua record thiếu DOI/title/summary | Completeness  |              (Tùy response raw) | Số lượng records raw vs clean |
| Parse lỗi ngày published | Validity                  |              (Tùy response raw) | Log filter trong script |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:
- `text_for_embedding`: Nối chuỗi thông tin gồm Title, Authors, Categories, Published Date và Summary để cung cấp ngữ cảnh đầy đủ nhất cho embedding.
- Document ID: `paper_id` được ép kiểu về dạng lowercase và bỏ các ký tự trắng thừa.
- `age_days`: Được tính bằng độ chênh lệch ngày giữa thời điểm run (run_date) và ngày published của record.

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | 24                 |
| Các`question_type`                    | summary, authors, date, categories |
| Ground-truth document ID                 | Từ clean dataframe     |
| Embedding model                          | default (MiniLM)                  |
| Vector store/collection                  | LocalEmbeddingIndex / ChromaDB |
| Retrieval`top_k`                       | 3 (default)                   |
| LLM provider/model                       | openai / gpt-4o-mini                   |
| Test set dùng chung cho ba trạng thái | b7541a16c52d730f8ea62e286e4eb3cded2638c0f5bb2b1838ca0e6ce1825872 |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:
Frozen test set đảm bảo tính công bằng khi đánh giá. Các câu hỏi được cố định dựa trên clean data chuẩn nhất ban đầu. Nhờ thế khi data bị hỏng (corrupted) và phục hồi lại (repaired), ta đo lường được xem hệ thống LLM/RAG còn trả lời chuẩn xác được các câu hỏi tham chiếu đó hay không.

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | Có |  |
| Cleaned dataset          | `data/clean/`                        | Có |  |
| Embedding manifest/index | `data/embeddings/`                   | Có |  |
| Evaluation set           | `data/eval/`                         | Có |  |
| Baseline metrics         | `data/results/baseline_metrics.json` | Có |  |
| Quality/freshness        | `data/quality/`                      | Có |  |
| Baseline report          | `data/reports/phase1_report.md`      | Có |  |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     1.0000 | Tỉ lệ retriever fetch đúng chunk Ground Truth  |
| `mean_token_f1`      |     0.0719 | F1 Token Overlap score                         |
| `judge_accuracy`     |     0.9167 | Độ chính xác của LLM Judge khi so khớp (1: Correct, 0: Sai) |
| `mean_judge_score`   |     4.8333 | Điểm đánh giá (1-5) của LLM Judge |
| Ragas      | N/A | Được tích hợp, nhưng trả về 0.0 trong lần chạy này do config hoặc environment missing ragas integration. |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| Expect_column_values_to_not_be_null | Completeness       | 100%         | PASS | `data/quality/gx/` |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | clean dataset / `age_days`           |
| Trạng thái baseline      | FRESH               |
| Lý do                     | Các bài viết từ crossref query đều đáp ứng đủ ngưỡng date/threshold |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| drop_records | Xoá row  |          3 | FAIL (số lượng/thiếu hụt) | Hit rate giảm mạnh | Rebuild từ snapshot |
| blank_summary | Làm trống cột summary | 1 | FAIL (Completeness) | Giảm context chất lượng | Rebuild từ snapshot |
| inject_noise | Ghi nhiễu rác | 1 | FAIL (Validity) | Giảm F1 và Judge Score | Rebuild từ snapshot |
| truncate_title | Cắt xén title | 1 | - | RAG trả lời sai hoặc F1 giảm | Rebuild từ snapshot |
| stale_published | Đẩy lùi date | 6 | STALE (Freshness) | Báo động Freshness | Rebuild từ snapshot |
| duplicate_rows | Clone rows | 1 | FAIL (Uniqueness) | Tăng noise/làm sai index | Rebuild từ snapshot |

Corruption log:
- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: Có
- Nhận xét: Đầy đủ các phép biến đổi mô phỏng sự cố dữ liệu thực tế.

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:
Repair không cố gắng chắp vá trên dữ liệu Corrupted (tránh error propagation), mà thực hiện xóa sạch Index lỗi, tải lại raw snapshot (nguồn nguyên thủy từ API đã lưu `data/raw/raw_records.json`), chạy lại toàn bộ pipeline cleaning và re-indexing.

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |      1.0 |       0.33 |      1.0 |                      -0.67 |             +0.67 | Repair khôi phục hoàn hảo |
| `mean_token_f1`        |      0.0719 |       0.02 |      0.0710 |                      -0.0519 |             +0.0510 | Điểm hồi phục về sát mức gốc |
| `judge_accuracy`       |      0.9167 |       0.1667 |      0.8750 |                      -0.75 |             +0.708 | Phục hồi rất tốt |
| `mean_judge_score`     |      4.8333 |       1.7917 |      4.7083 |                      -3.0416 |             +2.916 | Phục hồi rất tốt |
| Quality checks pass/fail |      PASS |       FAIL |      PASS |                      FAIL |             PASS | Quality rules được đáp ứng lại |
| Freshness status         |      FRESH |       STALE |      FRESH |                      STALE |             FRESH | Cập nhật được ngày tháng cũ |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:
1. Data change (Corruption: drop_records & inject_noise) → quality signal (FAIL rules) → retrieval metric giảm (Hit rate rớt từ 1.0 xuống 0.33).
2. Repair action (rebuild từ raw snapshot) → quality/freshness recovery (trở lại PASS/FRESH) → agent metric recovery (Hit rate khôi phục 1.0, Judge Accuracy khôi phục ~0.875).

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:
- **Triệu chứng:** Pipeline báo STALE freshness nhưng không rõ row nào gây ra trong quá trình đánh giá.
- **Nguyên nhân:** Logic tính toán age_days giữa các node xử lý bị lệch múi giờ (Timezone naive vs UTC aware).
- **Cách xử lý:** Chuẩn hóa toàn bộ parser datetime về dạng có chứa thông tin UTC (`utc=True` trong pandas).

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| Repair mất nhiều thời gian nếu source to | Quá trình Re-indexing chậm | Tích hợp incremental indexing thay vì rebuild toàn bộ. |
| Ragas trả về 0.0 do config LLM/VertexAI | Không quan sát được metrics faithfulness/relevancy chi tiết | Bổ sung fallback shim ổn định hơn cho Ragas package hoặc thay package version. |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [x] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [x] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [x] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
