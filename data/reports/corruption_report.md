# Báo cáo So sánh Làm nhiễu và Phục hồi

Mã băm SHA-256 của tập kiểm thử cố định cho mọi trạng thái: `b7541a16c52d730f8ea62e286e4eb3cded2638c0f5bb2b1838ca0e6ce1825872`

## So sánh chỉ số (Metric)

| Chỉ số | Baseline | Làm nhiễu | Phục hồi | Thay đổi khi nhiễu | Thay đổi khi phục hồi |
| --- | ---: | ---: | ---: | ---: | ---: |
| `retrieval_hit_rate` | 1.0000 | 0.3333 | 0.1667 | -0.6667 | -0.1667 |
| `mean_token_f1` | 0.0710 | 0.0200 | 0.0202 | -0.0510 | +0.0001 |
| `judge_accuracy` | 0.8750 | 0.1667 | 0.0833 | -0.7083 | -0.0833 |
| `mean_judge_score` | 4.7083 | 1.7917 | 1.4167 | -2.9167 | -0.3750 |

## So sánh khả năng quan sát (Observability)

| Tín hiệu | Làm nhiễu | Phục hồi |
| --- | --- | --- |
| Trạng thái chất lượng | KHÔNG ĐẠT (5 lỗi) | KHÔNG ĐẠT (1 lỗi) |
| Trạng thái độ tươi mới | STALE (7 dòng quá hạn) | STALE (4 dòng quá hạn) |

## Kết luận dựa trên bằng chứng

1. Việc làm nhiễu có kiểm soát đã làm thay đổi các tín hiệu về tính đầy đủ, tính duy nhất, tính hợp lệ và độ tươi mới, đồng thời làm giảm các chỉ số truy xuất/trả lời trên tập kiểm thử không bị thay đổi.
2. Việc xây dựng lại tập dữ liệu sạch từ bản lưu thô ban đầu đã khôi phục các tín hiệu chất lượng dữ liệu và phục hồi các chỉ số đánh giá mà không cần chỉnh sửa câu trả lời hay file chỉ số nào.
