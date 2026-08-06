# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin       | Nội dung                                    |
| --------------- | ------------------------------------------- |
| Họ và tên       | Trương Minh Hoàng                           |
| MSSV            | 2A202601262                                 |
| Khóa/Lớp        | K4-DAY10                                    |
| Tên nhóm        | Group 1                                     |
| Vai trò chính   | Data Analyst / QA                           |
| Repository      | https://github.com/mazzaw24/Day10_D303_B2-1 |
| Ngày hoàn thành | 2026-08-06                                  |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable                         | File/hàm phụ trách                                               | Input nhận vào   | Output bàn giao                   | Trạng thái |
| ------------------------------------------ | ---------------------------------------------------------------- | ---------------- | --------------------------------- | ---------- |
| Data Quality Checks, Freshness Constraints | `src/observability/quality.py`, `src/observability/freshness.py` | Parsed Records   | JSON Reports (Quality, Freshness) | Hoàn thành |
| Pipeline Validation                        | `tests/`                                                         | Pipeline Scripts | Kết quả Pytest                    | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động               | Thành viên/module được hỗ trợ | Kết quả                                                     |
| ----------------------- | ----------------------------- | ----------------------------------------------------------- |
| Review code và tích hợp | Đào Trung Hiếu / Team Leader  | Đảm bảo code observability được gọi đúng chỗ trong Pipeline |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện                            | File/hàm/artifact liên quan      | Kết quả bàn giao          | Cách xác minh                    |
| ------------------------------------------------ | -------------------------------- | ------------------------- | -------------------------------- |
| Cấu hình Great Expectations (GX) để check schema | `src/observability/quality.py`   | Báo cáo PASS/FAIL rõ ràng | Xem file `baseline_quality.json` |
| Cấu hình logic check năm xuất bản                | `src/observability/freshness.py` | Báo cáo FRESH/STALE       | Xem file `freshness_report.json` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Thư mục `data/quality/` tự động sinh ra các file JSON theo dõi sức khỏe dữ liệu sau mỗi luồng Baseline, Corrupted và Repaired. Nó đóng vai trò "còi báo động" (alert) khi dữ liệu có vấn đề.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Làm thế nào để phát hiện dữ liệu hỏng trước khi nó đi sâu vào model và làm hư kết quả sinh văn bản của LLM? Trả lời: Bằng cách áp dụng Data Observability (Kiểm tra chất lượng và độ tươi mới ngay lập tức).

### Cách triển khai

Tôi đã cài đặt Great Expectations (GX) để kiểm tra các rule cơ bản: trường `title` không được trống, trường `abstract` phải có độ dài nhất định, và dữ liệu phải đúng định dạng ngày tháng. Đồng thời, hàm `freshness.py` sẽ so sánh `published_date` của từng record với ngưỡng thời gian (ví dụ 3 năm) để đánh dấu các row bị "stale" (cũ).

### Input, output và contract

| Thành phần              | Mô tả                                                            |
| ----------------------- | ---------------------------------------------------------------- |
| Input                   | Danh sách dict dữ liệu từ quá trình ingestion                    |
| Output                  | Dict kết quả chất lượng (success: bool, failed_checks: int, ...) |
| Module phụ thuộc        | `great_expectations`, `datetime`                                 |
| Module sử dụng output   | Reporting Module                                                 |
| Điều kiện lỗi cần xử lý | Dữ liệu không có field cần check, ngày tháng sai format          |

### Cách xác minh

```bash
python -m pytest -q
```

- **Kết quả mong đợi:** Tất cả các test cases đi qua, chứng minh logic validate hoạt động tốt.
- **Kết quả thực tế:** Tests passed. File quality check `corrupted_quality.json` trả về FAIL.
- **Artifact/log:** `data/quality/baseline_quality.json`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Định nghĩa "độ tươi mới" (Freshness) cho các bài báo khoa học.
- **Các phương án đã cân nhắc:** (1) Dựa vào thời gian lưu file. (2) Dựa vào trường `published_date` thực tế trong bài báo.
- **Phương án đã chọn:** Dựa vào `published_date`.
- **Lý do:** Thời gian nạp dữ liệu (ingestion time) không phản ánh nội dung bài báo có lỗi thời hay không. Logic check dựa vào ngày xuất bản thực mới bảo vệ RAG khỏi việc sử dụng kiến thức quá đát.
- **Bằng chứng quyết định phù hợp:** Lúc chạy corruption, khi tôi cố tình lùi ngày xuất bản về năm 1990, hệ thống báo `STALE` ngay lập tức.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** GX báo lỗi khi chạy trên dữ liệu trống (empty list).
- **Lệnh hoặc bước tái hiện:** Chạy quality check khi quá trình ingestion bị fail.
- **Nguyên nhân gốc:** Không kiểm tra đầu vào trước khi validate.
- **Cách xử lý:** Thêm early return `if not records: return {'success': False, 'status': 'EMPTY'}`.
- **Cách xác minh sau khi sửa:** Chạy test case với dữ liệu trống, script không crash mà trả ra alert gọn gàng.
- **Điều học được:** Data Observability tool cũng cần phải robust (vững chắc) trước mọi dạng dữ liệu rác.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
   Trả lời: Tải JSON thô -> Trích xuất text -> Kiểm tra Quality -> Đưa vào FAISS.
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
   Trả lời: Các ID tài liệu chuẩn này giúp ta biết được Engine tìm kiếm có mò đúng bài báo cần thiết hay không.
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
   Trả lời: Quality check rà soát format, schema. Freshness rà soát tính cập nhật thời gian.
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
   Trả lời: Để tạo ra Control Group chuẩn mực, giúp so sánh chính xác sự lên xuống của metrics do dữ liệu thay đổi.
5. Repair được xem là thành công dựa trên artifact và metric nào?
   Trả lời: Data Quality báo PASS lại, Hit Rate và Judge Accuracy tăng lại mức bằng hoặc sát Baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal        | Baseline | Corrupted | Repaired | Nhận xét của cá nhân                                |
| -------------------- | -------: | --------: | -------: | --------------------------------------------------- |
| `retrieval_hit_rate` |   1.0000 |    0.3333 |   1.0000 | QA xác nhận hệ thống phục hồi                       |
| `mean_token_f1`      |   0.0719 |    0.0200 |   0.0710 | QA xác nhận hệ thống phục hồi                       |
| `judge_accuracy`     |   0.9167 |    0.1667 |   0.8750 | QA xác nhận hệ thống phục hồi                       |
| `mean_judge_score`   |   4.8333 |    1.7917 |   4.7083 | QA xác nhận hệ thống phục hồi                       |
| Quality checks       |     PASS |      FAIL |     PASS | Đúng mong đợi                                       |
| Freshness status     |    FRESH |     STALE |    FRESH | Báo cáo STALE có 7 stale rows, đúng như đã cấu hình |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. Data corruption (duplicate, drop, noise) → quality/freshness signal thay đổi (FAIL, STALE) → agent metric thay đổi (Rớt mạnh).
2. Repair action → quality/freshness signal phục hồi (PASS, FRESH) → agent metric phục hồi (Tiệm cận Baseline).

Corruption nào ảnh hưởng rõ nhất và vì sao?

Tất cả các dạng corruption đều phản ánh trực tiếp lên Quality Status. Nhưng `stale_published` là thứ chỉ có Observability Module (Freshness) mới bắt được, nếu không LLM vẫn sẽ sinh ra câu trả lời sai về mặt thời gian (knowledge cutoff drift).

Kết quả nào khác với kỳ vọng ban đầu?

Tôi từng kỳ vọng hệ thống sẽ tự chặn không cho chạy Evaluation nếu Quality FAIL (Circuit Breaker). Tuy nhiên trong lab này, pipeline vẫn chạy tiếp để đo lường mức độ ảnh hưởng của dữ liệu hỏng lên metrics (theo đúng yêu cầu của giáo viên).

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Thấu hiểu được cách viết Unit Tests cho Data Pipeline.
2. Hiểu rõ sức mạnh của Data Observability thông qua Great Expectations.
3. RAG là một chuỗi cung ứng dữ liệu (data supply chain), hỏng ở đâu là đầu ra điêu đứng ở đó.

### Nếu có thêm thời gian

Tôi sẽ cài đặt cảnh báo Slack/Email webhook. Bất cứ khi nào Quality Check rớt trạng thái FAIL, hệ thống sẽ tự động bắn tin nhắn về kênh Slack cho team biết ngay.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trương Minh Hoàng
**Ngày xác nhận:** 2026-08-06
