# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Phạm Thế Đăng             |
| MSSV               | 2A202601766                     |
| Khóa/Lớp         | D303B2-1               |
| Tên nhóm         | B2-1    |
| Vai trò chính    | Documentation / AI Ops                 |
| Repository         | https://github.com/Dao-Trung-Hieu-2912/K3-DAY10-2A202601238-DaoTrungHieu |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| Result Analysis, Reporting, Observability Evidence | `src/observability/reporting.py`, `script/generate_submission_reports.py` | JSON Metrics, Quality Reports | Markdown Reports, Dashboard | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| Setup môi trường và Document | Cả nhóm | Toàn bộ repo được README hướng dẫn kỹ, cài đặt qua `uv` mượt mà |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Xây dựng báo cáo tự động bằng Python Markdown Generation | `src/observability/reporting.py` | Các file `.md` tại `data/reports/` | Đọc các file báo cáo sinh ra |
| Xây dựng cơ chế điền mẫu báo cáo cá nhân tự động | `script/generate_submission_reports.py` | Tự động sinh báo cáo cá nhân và nhóm | Lệnh chạy không lỗi và sinh đủ file |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Thư mục `data/reports/` chứa `phase1_report.md` và `corruption_report.md`. Đây là các "bằng chứng sống" (evidence-based artifacts) tự động sinh ra sau mỗi lần code chạy, không cần con người nhúng tay, rất tốt cho quá trình vận hành AI Ops.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Lập trình viên và AI engineers thường chạy test sinh ra một đống file JSON kết quả nhưng rất khó đọc. Cần một module sinh báo cáo trực quan dạng Markdown (và SVG) để con người (stakeholders) có thể nhìn vào và biết ngay Pipeline đang hoạt động tốt hay không.

### Cách triển khai

Tôi tận dụng Python f-strings và các hàm xử lý chuỗi cơ bản để đọc file JSON kết quả, trích xuất metrics (Hit Rate, F1, Judge Score), Quality checks (Pass/Fail) và render thành chuỗi Markdown. Tôi đặc biệt chú ý giữ các báo cáo sinh ra theo form chuẩn và cấu trúc rõ ràng.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Các file JSON kết quả từ thư mục `data/results/` và `data/quality/` |
| Output                         | Markdown Reports, Visualization (SVG) |
| Module phụ thuộc             | Python chuẩn, không dùng thư viện ngoài |
| Module sử dụng output        | Giáo viên chấm điểm / Team xem xét kết quả |
| Điều kiện lỗi cần xử lý | File JSON không tồn tại do luồng trước đó chết |

### Cách xác minh

```bash
python script/generate_submission_reports.py
```

- **Kết quả mong đợi:** Tất cả các báo cáo nhóm và cá nhân được fill thành công.
- **Kết quả thực tế:** Các file báo cáo được sinh ra hoàn chỉnh trong folder `report/`.
- **Artifact/log:** `report/group_report.md` và các báo cáo cá nhân.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Báo cáo so sánh sự cố (corruption report) cần nêu bật được độ thay đổi (%) của metrics.
- **Các phương án đã cân nhắc:** (1) Dùng LLM viết giải thích văn xuôi. (2) Render một bảng Hard-coded Markdown Comparison.
- **Phương án đã chọn:** Dùng cả hai. Bảng Markdown tĩnh cho con người dễ nhìn số liệu, và một chút nhận xét logic được điền vào.
- **Lý do:** Trade-off giữa sự tường minh và sự tốn kém. Bảng tĩnh rẻ, không cần gọi API. 
- **Bằng chứng quyết định phù hợp:** File `corruption_report.md` đọc rất rõ ràng, mức tăng giảm thể hiện ngay trên bảng.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Lỗi unicode (font) `UnicodeEncodeError` hoặc không hiển thị đúng các chữ `Đ` trong tên thành viên người Việt.
- **Lệnh hoặc bước tái hiện:** Chạy hàm tạo tên file an toàn (safe_name) trên các tên có dấu tiếng Việt.
- **Nguyên nhân gốc:** Thư viện `unicodedata` không coi chữ `Đ` là chữ D có thêm dấu (diacritic) mà là một ký tự độc lập, nên `NFD` normalization loại bỏ hẳn nó ra khỏi tên tiếng Anh.
- **Cách xử lý:** Thêm hàm replace thủ công `name.replace('Đ', 'D').replace('đ', 'd')` trước khi chuẩn hóa.
- **Cách xác minh sau khi sửa:** Tên file sinh ra chuẩn xác `2A202601766_PhamTheDang.md` thay vì `PhamTheang`.
- **Điều học được:** Xử lý chuỗi Unicode đa ngôn ngữ luôn tiềm ẩn các edge-cases phải xử lý bằng tay.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
Trả lời: Gọi API lấy JSON -> Parser text -> Model text-embedding-MiniLM -> FAISS Index.
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
Trả lời: Ground-truth đóng vai trò "đáp án đúng". Bất cứ kết quả retrieval hoặc generation nào sai lệch với nó đều bị trừ điểm.
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
Trả lời: Cùng nằm trong module Observability nhưng Quality tập trung vào Integrity (tính toàn vẹn cấu trúc), còn Freshness tập trung vào Recency (tính cập nhật).
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
Trả lời: Để thực hiện Controlled Experiment (thí nghiệm đối chứng).
5. Repair được xem là thành công dựa trên artifact và metric nào?
Trả lời: Dựa vào việc so sánh Baseline Metrics JSON với Repaired Metrics JSON: Nếu chúng giống nhau (matches_baseline = True), repair thành công.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` | 1.0000 | 0.3333 | 1.0000 | Rất ấn tượng |
| `mean_token_f1`      | 0.0719 | 0.0200 | 0.0710 | Hơi thấp so với kỳ vọng |
| `judge_accuracy`     | 0.9167 | 0.1667 | 0.8750 | Hợp lý |
| `mean_judge_score`   | 4.8333 | 1.7917 | 4.7083 | Phản ánh chính xác chất lượng |
| Quality checks         | PASS | FAIL | PASS | Đúng với thiết kế |
| Freshness status       | FRESH | STALE | FRESH | Đúng với thiết kế |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. Data corruption → quality/freshness signal thay đổi (Báo lỗi Data Observability) → agent metric thay đổi (RAG trả lời bậy bạ).
2. Repair action → quality/freshness signal phục hồi (Không còn cảnh báo lỗi) → agent metric phục hồi (RAG thông thái trở lại).

Corruption nào ảnh hưởng rõ nhất và vì sao?

Lỗi tiêm nhiễu văn bản (inject_noise) vào abstract làm RAG agent bị "mù chữ". Tuy Retrieval có thể vẫn mò ra bài báo nếu search dựa trên title, nhưng đoạn văn mang ra cho LLM đọc bị mã hóa (garbage text), dẫn đến LLM sinh câu trả lời vô nghĩa. 

Kết quả nào khác với kỳ vọng ban đầu?

Tôi đã nghĩ Repaired Metrics sẽ giống Baseline Metrics chính xác đến 100% (so sánh từng số thập phân). Thực tế nó gần giống (4.8333 vs 4.7083). Nguyên nhân là LLM là mạng nơ-ron xác suất, không hoàn toàn deterministic, nên mỗi lần chạy lại đều có slight variations.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. Mọi Pipeline chuyên nghiệp đều phải có Evidence / Báo cáo tự động hóa, tránh việc phải dò số liệu bằng mắt thủ công.
2. Việc chia role trong một dự án AI giúp chuyên môn hóa và tăng tốc độ code.
3. Luôn phải xử lý encoding tiếng Việt một cách cẩn thận.

### Nếu có thêm thời gian

Tôi sẽ viết thêm dashboard web tương tác (như Streamlit) thay vì chỉ xuất ra file Markdown tĩnh để người dùng có thể kéo thả và xem các báo cáo trực quan hơn.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Phạm Thế Đăng
**Ngày xác nhận:** 2026-08-06
