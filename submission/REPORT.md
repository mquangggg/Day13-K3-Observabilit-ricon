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

- Prompt name: `day13-chat`
- Version/label baseline: Version 1 (label: `baseline`, `production`)
- Version/label candidate: Version 2 (label: `candidate`, `production`)
- Trace ID của mỗi version: 
  - Trace ID (Version 1): `3986d27a852140f33fc2c258800668fa`
  - Trace ID (Version 2): `bc0300dde7832a3a903b66808a0a5155`
- Bằng chứng đổi label hoặc rollback: [prompt_versioning.png](evidence/prompt_versioning.png)

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

## 6. Điều tra challenge

- Challenge ID: `day13-k3-observability-v1`
- Triệu chứng từ metrics: Latency tăng vọt lên ~13,280 ms (vượt xa ngưỡng `latency_threshold_ms: 2000` ms) tập trung ở feature `refund`.
- Trace ID liên quan: `bc0300dde7832a3a903b66808a0a5155`
- Log line/correlation ID liên quan: `correlation_id` dạng `req-a13b9acd` (xác nhận trong `data/logs.jsonl` có event `response_sent` với latency vượt quá 10,000 ms).
- Root cause: Incident `rag_slow` kích hoạt làm nghẽn hàm `retrieve()` trong RAG module (`mock_rag.py`), gây delay 2.5s cho mỗi lần gọi retrieval và làm tích tụ độ trễ dưới tải đồng thời (concurrency = 5).
- Fix action: Tắt incident bằng cách gọi API `POST /incidents/rag_slow/disable` hoặc sửa tối ưu thời gian phản hồi của RAG service.
- Preventive measure: Cấu hình timeout cho bước RAG retrieval (ví dụ max timeout 1.0s kèm fallback cache/default context) và thiết lập Alert rule cảnh báo khi P95 RAG latency > 1500ms.

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| Phạm Trung Kiên (TV2) | Langfuse Tracing, Prompt Versioning & Rollback, Correlation ID trong Trace, Điều tra Challenge Traces | [phamkien branch](https://github.com/mquangggg/Day13-K3-Observabilit-ricon/tree/phamkien) | Cách quản lý phiên bản Prompt trên Langfuse Cloud, kết nối Traces → Logs qua correlation_id, phân tích waterfall trace để tìm nghẽn RAG. |
