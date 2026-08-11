# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm: ri con
- Repository URL: https://github.com/mquangggg/Day13-K3-Observabilit-ricon
- Commit SHA cuối: 1b74e47c53a61d61ce50f5752255a45190d21767
- Thành viên và vai trò:
  - Vũ Minh Quang 2A202601515 (Thành viên 1): Logging, Metadata & PII Redaction
  - Phạm Trung Kiên 2A202601525 (Thành viên 2): Tracing & Prompt Versioning (Langfuse)
  - Lương Ngọc Quang 2A202601563 (Thành viên 3): Dashboard, SLO, Alerting & Runbook

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100
- Tổng số traces:
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard: `config/dashboard.yaml` / `data/logs.jsonl`

## 3. Logging và tracing

- Evidence correlation ID: Tất cả các API request đều được gán `correlation_id` chuẩn dạng `req-<8-char-hex>` (ví dụ: `req-03c236aa`) truyền qua response header `x-request-id` và ghi đồng bộ trong `data/logs.jsonl`.
- Evidence PII redaction: Đã kích hoạt processor `scrub_event` trong `logging_config.py` và hàm `scrub_obj` trong `pii.py`. Tất cả Email, SĐT, CCCD, Số thẻ được thay thế bằng các token dạng `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, v.v.
- Evidence trace waterfall: [trace_waterfall.png](evidence/trace_waterfall.png)
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name: `day13-chat`
- Version/label baseline: Version 1 (label: `baseline`, `production`)
- Version/label candidate: Version 2 (label: `candidate`, `production`)
- Trace ID của mỗi version: 
  - Trace ID (Version 1): `3986d27a852140f33fc2c258800668fa`
  - Trace ID (Version 2): `bc0300dde7832a3a903b66808a0a5155`
- Bằng chứng đổi label hoặc rollback: [prompt_versioning.png](evidence/prompt_versioning.png)

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: HỢP LỆ: 6/6 panel có trong dashboard contract.
- Evidence dashboard: Nguồn dữ liệu từ `data/logs.jsonl` bao gồm 6 panels tiêu chuẩn:
  1. Latency Percentiles (P50, P95, P99 - ms) với threshold P95 <= 3000ms.
  2. Request Traffic (count & req/min) với threshold >= 1 req/min.
  3. Error Rate & Breakdown (%) với threshold Error Rate <= 2%.
  4. Cost Over Time (USD) với threshold Total <= $2.5.
  5. Input & Output Tokens với threshold <= 50,000 tokens.
  6. Quality Proxy (Quality Score 0-1) với threshold Mean >= 0.75.
- SLO đã chọn và lý do:
  - Latency SLO: P95 Latency <= 3000ms. Lý do: Đảm bảo trải nghiệm RAG/LLM cho người dùng không bị nghẽn (xuất hiện phản hồi dưới 3 giây).
  - Availability/Error Rate SLO: Error Rate <= 2%. Lý do: Giữ cho hệ thống agent ổn định, tỉ lệ lỗi hệ thống/LLM không vượt quá ngưỡng cho phép.
- Alert rules và runbook:
  - Alert 1: High Latency Alert (P95 > 3000ms trong 5 phút). Runbook: Kiểm tra RAG retrieval duration và LLM response time trên Langfuse trace waterfall. Nếu do RAG retry, kiểm tra kết nối vector store/RAG incident mock.
  - Alert 2: High Error Rate Alert (Error Rate > 2% trong 5 phút). Runbook: Lọc `data/logs.jsonl` theo `event == "request_failed"`, tìm `error_type` chính và xem `correlation_id` tương ứng trên Langfuse để xác định nguyên nhân crash.

## 6. Điều tra challenge

- Challenge ID: `day13-k3-observability-v1`
- Triệu chứng từ metrics: P95 Latency của feature `refund` bùng nổ lên tới 12,500ms - 15,200ms (vượt xa ngưỡng SLO 3,000ms).
- Trace ID liên quan: `req-8bc9c46b`, `req-2ae12e55`, `req-ebae43d7`, `req-f646b30a`, `req-59fc8772`
- Log line/correlation ID liên quan: `req-8bc9c46b` (Latency: 12545.2ms, `user_id_hash`: `026c7a407135`, feature: `refund`)
- Root cause: Do sự cố mock `rag_slow` (RAG Retrieval Service bị nghẽn/retry lặp lại), khiến thời gian tìm kiếm tài liệu tham khảo cho tính năng `refund` bị kéo dài thêm từ 5,000ms đến 10,000ms cho mỗi request.
- Fix action: Tắt sự cố mock `rag_slow` bằng cách gửi request POST `/incidents/rag_slow/disable` (hoặc chạy `python scripts/inject_incident.py --scenario rag_slow --disable`), đồng thời tối ưu timeout cho RAG retrieval service xuống 2,000ms.
- Preventive measure: Cấu hình Circuit Breaker và Fallback mechanism cho RAG Retrieval service (nếu RAG quá 2,000ms thì trả về câu trả lời mặc định hoặc dùng cache thay vì retry lãng phí latency).

## 7. Đóng góp cá nhân

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Vũ Minh Quang | Triển khai Correlation ID middleware, PII Redaction & Structured Logging | Commit `272dcba`, PR merge main | Hiểu rõ cơ chế propagation Correlation ID & PII scrubbing trong Structlog |
| Phạm Trung Kiên (TV2) | Tích hợp Tracing, Prompt Versioning & Rollback | Commit `78f4801`, PR merge main | Cách quản lý Prompt Versioning và truy vết Span trên Langfuse |
| Lương Ngọc Quang | Cấu hình Alerts, Dashboard Contract & Runbook | Commit `be61e1c`, PR merge main | Thiết lập SLO/Alert thresholds và xây dựng Dashboard contract từ logs.jsonl |
