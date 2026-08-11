# CP3 Checklist — Member C (QA & Chief Investigator)

**Vai trò:** Điều tra challenge chính thức, tổng hợp báo cáo, quản lý dashboard và load test.

---

## 📅 TRƯỚC 2:30 — Chuẩn bị sẵn

### Phần 1: Kiểm tra Dashboard & Validator
- [ ] Chạy `python scripts/validate_dashboard.py` → báo cáo kết quả
- [ ] Mở dashboard (Langfuse hoặc Streamlit) để quen giao diện
- [ ] Note lại 6 panel: Latency (P50/P95/P99), Traffic, Errors, Cost, Tokens, Quality
- [ ] Kiểm tra threshold/SLO line có hiển thị rõ không

### Phần 2: Baseline Load Test
- [ ] Chạy `python scripts/load_test.py --concurrency 5` → tạo baseline
- [ ] Ghi lại các metric hiện tại (để so sánh lúc incident):
  - [ ] P95 latency của feature `refund` (ms)
  - [ ] Error rate (%)
  - [ ] Cost total (USD)
  - [ ] Tokens in/out
  - [ ] Quality score mean
- [ ] Lưu ảnh/số liệu baseline vào `submission/evidence/baseline_metrics.txt`

### Phần 3: Chuẩn bị Khung Báo Cáo
- [ ] Mở template `submission/REPORT.md`
- [ ] Điền mục 1 (Thông tin nhóm) và mục 5 (Dashboard, SLO, alerts) từ CP2
- [ ] Tạo khung cho mục 6 (Điều tra challenge):
  ```markdown
  ## 6. Điều tra challenge
  - Challenge ID: [TBD - lấy từ config/challenge.json lúc 2:30]
  - Triệu chứng từ metrics: [TBD - chạy dashboard]
  - Trace ID liên quan: [TBD - trace ID sẽ điền sau]
  - Log line/correlation ID liên quan: [TBD - log sẽ điền sau]
  - Root cause: [TBD - phân tích trace & log]
  - Fix action: [TBD - đề xuất fix]
  - Preventive measure: [TBD - biện pháp phòng ngừa]
  ```

### Phần 4: Practice Incident (Luyện tập)
- [ ] Chạy `python scripts/inject_incident.py --scenario rag_slow` để kích hoạt incident mẫu
- [ ] Chạy `python scripts/load_test.py --concurrency 5` với incident đang kích hoạt
- [ ] Quan sát dashboard: latency, error rate có tăng không?
- [ ] Mở một trace chậm từ Langfuse
- [ ] Tìm span nào kéo dài bất thường (ví dụ: RAG, LLM call)
- [ ] Tìm log có cùng correlation ID
- [ ] Ghi lại luồng: Metrics → Trace → Log
- [ ] Tắt incident: `python scripts/inject_incident.py --scenario rag_slow --disable`

### Phần 5: Chuẩn bị Folder Evidence
- [ ] Tạo folder: `submission/evidence/cp3_challenge/`
- [ ] Chuẩn bị chỗ để lưu:
  - [ ] Ảnh/CSV dashboard lúc incident
  - [ ] Trace waterfall (JSON hoặc ảnh)
  - [ ] Log lines (text với correlation ID)
  - [ ] Kết quả validator

---

## 🚨 ĐÚ 2:30 — LÚC CHALLENGE RELEASE

### Bước 1: Nhận & Parse Challenge
- [ ] Lab Coach sẽ đẩy `config/challenge.json` lên repo hoặc công bố file
- [ ] Bạn pull về hoặc clone file
- [ ] Đọc file và ghi lại:
  ```json
  {
    "challenge_id": "day13-k3-observability-v1",
    "incident": "rag_slow",                          // ← Loại incident
    "affected_feature": "refund",                   // ← Feature bị ảnh hưởng
    "latency_threshold_ms": 2000,                   // ← Ngưỡng latency
    "queries": [...]                                // ← 5 test queries
  }
  ```

### Bước 2: Chạy Challenge Chính Thức
- [ ] Terminal 1: Chạy incident và load test
  ```bash
  python scripts/inject_incident.py
  python scripts/load_test.py --challenge --concurrency 5
  ```
- [ ] Terminal 2: Giữ API chạy (nếu chưa chạy)
  ```bash
  uvicorn app.main:app --reload --env-file .env
  ```
- [ ] Chờ load test hoàn tất (~1-2 phút)

### Bước 3: Ghi Lại Triệu Chứng từ Dashboard
- [ ] Mở dashboard và chọn time range vừa chạy load test
- [ ] **Latency panel:**
  - [ ] Ghi P95 (ms) — phải vượt 2000 ms hay gần gần
  - [ ] Ghi P99 (ms)
  - [ ] Ảnh chụp panel
- [ ] **Error rate panel:**
  - [ ] Có tăng đột ngột không?
  - [ ] Error type là gì (timeout, RAG, LLM)?
- [ ] **Traffic panel:**
  - [ ] Requests/phút là bao nhiêu
  - [ ] So sánh với baseline
- [ ] **Cost & Tokens panel:**
  - [ ] Có tăng vì incident không?
- [ ] **Quality score:**
  - [ ] Có giảm không?
- [ ] Lưu ảnh tất cả 6 panel vào `submission/evidence/cp3_challenge/dashboard_incident.png`

---

## 🔍 2:45–3:00 — ĐIỀU TRA TRACE

### Bước 1: Tìm Trace Chậm
- [ ] Mở Langfuse (hoặc trace view)
- [ ] Lọc theo feature `refund` và time range của load test
- [ ] Tìm trace với latency cao nhất (phải > 2000 ms hay gần)
- [ ] Ghi lại **Trace ID**: `__________________________`

### Bước 2: Phân Tích Span
- [ ] Mở trace waterfall
- [ ] Tìm span nào kéo dài bất thường:
  - [ ] `rag_retrieval` span (nên < 500 ms, nếu > 1000 ms là bất thường)
  - [ ] `llm_call` span (nên < 1000 ms)
  - [ ] `middleware` span (nên < 100 ms)
- [ ] Ghi lại span bất thường:
  - Span name: `__________________________`
  - Duration: `______ ms` (so sánh baseline)
  - Metadata: `__________________________`
- [ ] Chụp ảnh waterfall: `submission/evidence/cp3_challenge/trace_waterfall.png`

### Bước 3: Kiểm Tra Metadata
- [ ] Mở trace metadata:
  - [ ] `prompt_name` và `prompt_version` là gì?
  - [ ] `model` là gì?
  - [ ] `feature` là `refund` không?
  - [ ] Có log line count không?

---

## 📋 3:00–3:15 — ĐIỀU TRA LOG

### Bước 1: Tìm Log Cùng Correlation ID
- [ ] Lấy **correlation ID** từ trace metadata (`x-request-id`)
- [ ] Mở `data/logs.jsonl` (file text hoặc grep)
- [ ] Tìm tất cả log line có correlation ID này:
  ```bash
  grep "correlation_id" data/logs.jsonl | grep "<TRACE_ID>"
  ```
- [ ] Ghi lại tất cả log line vào `submission/evidence/cp3_challenge/logs_incident.txt`

### Bước 2: Phân Tích Log
- [ ] Đọc log theo thứ tự thời gian:
  - [ ] `request_received` — lấy timestamp bắt đầu
  - [ ] `middleware_start` — khi middleware gán correlation ID
  - [ ] Log từ agent (nếu có)
  - [ ] Log từ RAG/LLM call (đây là chỗ chậm!)
  - [ ] `response_sent` — khi hoàn tất
- [ ] Tìm log line nào cho biết incident (ví dụ: "RAG latency exceeds threshold", "LLM timeout", "cache miss")
- [ ] Ghi lại log line bất thường:
  ```
  timestamp: ____________________
  event: ____________________
  message: ____________________
  span_name: ____________________
  duration_ms: ____________________
  ```

### Bước 3: Ghép Trace & Log
- [ ] Xác nhận:
  - [ ] Span bất thường trong trace có match với log không?
  - [ ] Duration trong trace và log có khớp không?
  - [ ] Root cause có được nhắc đến trong log không?

---

## 🎯 3:15–3:25 — XÁC ĐỊNH ROOT CAUSE

### Lựa Chọn Root Cause (dựa trên incident `rag_slow`)
Với `rag_slow`, nguyên nhân có thể là:
1. **RAG retrieval quá chậm** — database query, embedding, hoặc network latency
2. **LLM context quá lớn** — vì RAG trả về quá nhiều document, LLM mất thời gian xử lý
3. **Cache miss** — nếu có cache, incident tắt cache hoặc làm cache invalid
4. **Concurrency quá cao** — resource contention (CPU, memory)

### Ghi Lại Root Cause
- [ ] Nguyên nhân chính: `____________________________________`
- [ ] Bằng chứng từ metrics: `____________________________________`
  - Ví dụ: "P95 latency tăng từ 300ms → 2500ms"
- [ ] Bằng chứng từ trace: `____________________________________`
  - Ví dụ: "rag_retrieval span từ 150ms → 1800ms"
- [ ] Bằng chứng từ log: `____________________________________`
  - Ví dụ: "log line: 'RAG query took 1.8s, expected < 500ms'"

---

## ✅ 3:25–3:35 — TỰ KIỂM TRA & HOÀN THIỆN

### Bước 1: Chạy Lại Validator
- [ ] `python scripts/validate_logs.py` → ghi lại điểm (nên ≥ 80/100)
- [ ] `python scripts/validate_dashboard.py` → nên báo `6/6 panel`
- [ ] `python -m pytest -q` → nên qua tất cả test

### Bước 2: Hoàn Thiện Báo Cáo
- [ ] Mở `submission/REPORT.md`
- [ ] Điền mục 6 (Điều tra challenge):
  ```markdown
  - Challenge ID: day13-k3-observability-v1
  - Triệu chứng từ metrics: P95 latency tăng từ XXXms → YYYms; error rate ZZ%
  - Trace ID liên quan: [TRACE_ID]
  - Log line/correlation ID: [CORRELATION_ID]
  - Root cause: [Mô tả chi tiết, kèm bằng chứng]
  - Fix action: [Đề xuất fix, ví dụ: tăng timeout, tối ưu RAG query, v.v.]
  - Preventive measure: [Biện pháp phòng ngừa tái diễn, ví dụ: monitoring, alerting, caching, v.v.]
  ```
- [ ] Điền mục 7 (Đóng góp cá nhân):
  - Ghi rõ vai trò và điều đã làm

### Bước 3: Kiểm Tra Evidence
- [ ] `submission/evidence/` có những file:
  - [ ] `baseline_metrics.txt` (hoặc CSV)
  - [ ] `cp3_challenge/dashboard_incident.png`
  - [ ] `cp3_challenge/trace_waterfall.png`
  - [ ] `cp3_challenge/logs_incident.txt`
  - [ ] Các file từ CP2 (nếu chưa có)

### Bước 4: Kiểm Tra Không Lộ Secret/PII
- [ ] `git status` → kiểm tra `.env` không bị commit
- [ ] `grep -r "LANGFUSE_SECRET_KEY" submission/` → không được lộ key
- [ ] `grep -r "@gmail\|0[0-9]{9}" submission/evidence/` → không được lộ email, SĐT (nếu có)
- [ ] Các log trong evidence phải đã được scrub PII

### Bước 5: Commit & Push
- [ ] `git add submission/`
- [ ] `git commit -m "CP3: Challenge investigation - root cause identified"`
- [ ] `git push origin main`
- [ ] Ghi lại **commit SHA**: `____________________________________`

---

## 📝 3:35–4:00 — CHUẨN BỊ DEMO & HOÀN TẤT

### Bước 1: Viết Runbook Demo
- [ ] Viết một đoạn 5-10 dòng mô tả cách demo:
  ```
  1. Mở dashboard, xem metric baseline
  2. Chạy `python scripts/inject_incident.py` + `python scripts/load_test.py --challenge`
  3. Dashboard cập nhật → chỉ ra latency tăng
  4. Mở trace [TRACE_ID] → chỉ ra span RAG chậm
  5. Mở log [CORRELATION_ID] → chỉ ra log line bằng chứng
  6. Nêu root cause + fix + preventive measure
  ```

### Bước 2: Chuẩn Bị Slide (nếu cần)
- [ ] 1 slide dashboard (baseline + incident)
- [ ] 1 slide trace waterfall
- [ ] 1 slide log & root cause
- [ ] 1 slide fix + preventive measure

### Bước 3: Final Check
- [ ] Báo cáo đầy đủ tất cả 7 mục
- [ ] Evidence đủ: metrics, trace, log, dashboard
- [ ] Không lộ secret/PII
- [ ] Git clean (commit SHA, branch main)

---

## 🎯 Kết Quả Cuối Cùng

**File nộp bắt buộc:**
- [x] `submission/REPORT.md` — báo cáo đầy đủ
- [x] `submission/evidence/` — ảnh/file bằng chứng
- [x] Git repo URL + commit SHA cuối

**Evidence CP3:**
- [x] Dashboard (6 panel, có threshold)
- [x] Trace ID (waterfall, span bất thường)
- [x] Log lines (correlation ID, event bất thường)
- [x] Root cause (bằng chứng từ 3 lớp: metrics, trace, log)
- [x] Fix & preventive measure

---

**Chúc bạn thành công! 🚀**
