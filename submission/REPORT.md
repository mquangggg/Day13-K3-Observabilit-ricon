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
  - Trace ID (Version 1): `6b1d0b6d64a6251283b335484bb41504`
  - Trace ID (Version 2): `06d42653e692ebb60a76c9acb3eef6bf`
- Bằng chứng đổi label hoặc rollback: [prompt_versioning.png](evidence/prompt_versioning.png)

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`:
- Evidence dashboard:
- SLO đã chọn và lý do:
- Alert rules và runbook:

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
