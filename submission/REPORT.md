# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: 100/100
- Tổng số traces:
- Số PII leak còn lại: 0
- Link/đường dẫn dashboard:

## 3. Logging và tracing

- Evidence correlation ID: Tất cả các API request đều được gán `correlation_id` chuẩn dạng `req-<8-char-hex>` (ví dụ: `req-03c236aa`) truyền qua response header `x-request-id` và ghi đồng bộ trong `data/logs.jsonl`.
- Evidence PII redaction: Đã kích hoạt processor `scrub_event` trong `logging_config.py` và hàm `scrub_obj` trong `pii.py`. Tất cả Email, SĐT, CCCD, Số thẻ được thay thế bằng các token dạng `[REDACTED_EMAIL]`, `[REDACTED_PHONE_VN]`, v.v.
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

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

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| | | | |
