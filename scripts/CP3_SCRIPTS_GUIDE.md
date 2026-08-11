# CP3 Investigation Scripts — Quick Guide

**3 script giúp bạn điều tra incident CP3 nhanh:**

1. **`investigate_incident.py`** — Lọc log theo feature, correlation ID, hoặc time range
2. **`read_traces.py`** — Đọc trace từ Langfuse, phân tích span chậm
3. **`summarize_incident.py`** — Tóm tắt toàn bộ: metrics → trace → log → root cause

---

## 📋 Sử Dụng Từng Script

### 1️⃣ **investigate_incident.py** — Lọc & Phân Tích Log

**Mục đích:** Tìm slow requests, failed requests, phân tích span latency.

**Lệnh cơ bản:**

```bash
# Tìm slowest requests trong feature 'refund' với threshold 2000ms
python scripts/investigate_incident.py --feature refund --threshold 2000

# Lọc log theo correlation ID (để xem chi tiết 1 request)
python scripts/investigate_incident.py --correlation-id req-03c236aa

# Tìm tất cả slow requests
python scripts/investigate_incident.py --slow
```

**Output example:**

```
🔍 **Step 1: Slow Requests** (latency > 2000ms)
Found 3 slow request(s) in feature 'refund':

  1. Correlation ID: req-03c236aa
     Latency: 2547ms ⚠️
     Feature: refund
     User: user_hash_123
     Time: 2026-08-11T14:35:22Z

🔍 **Step 2: Span Analysis** (Correlation ID: req-03c236aa)
Span breakdown for slowest request:

  📍 rag_retrieval
     Total: 1800ms | Avg: 1800ms | Max: 1800ms | Calls: 1
     ⚠️  THIS SPAN IS ABNORMAL!

  📍 llm_call
     Total: 600ms | Avg: 600ms | Max: 600ms | Calls: 1

  📍 middleware
     Total: 50ms | Avg: 50ms | Max: 50ms | Calls: 1
```

**Khi nào dùng:**
- Lần đầu tiên chạy load test → tìm slow requests
- Muốn xem chi tiết 1 request cụ thể → dùng `--correlation-id`
- Muốn so sánh latency các span → kết quả Step 2

---

### 2️⃣ **read_traces.py** — Đọc Trace từ Langfuse

**Mục đích:** Lấy trace waterfall, phân tích span, xem metadata.

**Lệnh cơ bản:**

```bash
# Đọc trace từ Langfuse (cần trace ID)
python scripts/read_traces.py --trace-id abc123xyz

# Lấy traces cho feature 'refund' (limit 10)
python scripts/read_traces.py --feature refund --limit 10
```

**Output example:**

```
📍 Trace ID: trace-abc123xyz
   Input: {"message": "What is your refund policy?", "feature": "refund"}
   Output: {"response": "..."}
   Metadata: {"prompt_name": "refund-qa", "prompt_version": "v1"}

✅ rag_retrieval [+150ms] 1800ms
   Metadata: {"documents_retrieved": 5, "retrieval_time": 1800}

✅ llm_call [+1950ms] 600ms
   Metadata: {"model": "gpt-4", "tokens": 150}

🔍 SLOW SPANS ANALYSIS

Found 1 slow span(s):

  1. rag_retrieval
     Duration: 1800.0ms ⚠️
     Status: success
     Metadata: {"documents_retrieved": 5, "retrieval_time": 1800}
```

**Khi nào dùng:**
- Khi bạn có trace ID từ dashboard → tìm trace detail
- Muốn xem waterfall của request → hiểu flow
- Muốn ghép trace metadata với log → check prompt version, model, v.v.

---

### 3️⃣ **summarize_incident.py** — Tóm Tắt Toàn Bộ Incident

**Mục đích:** Nối luôn metrics → trace → log → root cause → recommended actions.

**Lệnh:**

```bash
python scripts/summarize_incident.py
```

**Output:** File `submission/evidence/cp3_incident_summary.md` chứa:

```markdown
## 1. Challenge Configuration
Challenge ID: day13-k3-observability-v1
Incident Type: rag_slow
Affected Feature: refund
Latency Threshold: 2000ms

## 2. Symptoms Detected (from Metrics)
  ⚠️  P95 latency (2547ms) exceeds threshold (2000ms)
  ⚠️  Error rate: 0.0%

## 3. Metrics Summary
  Total Requests: 5
  P50 Latency: 300ms
  P95 Latency: 2547ms ← **KEY METRIC**
  P99 Latency: 2547ms
  Threshold: 2000ms

## 4. Slowest Requests
  1. Correlation ID: **req-03c236aa**
     Latency: 2547ms
     Timestamp: 2026-08-11T14:35:22Z

## 5. Trace Analysis — Span Breakdown
  📍 **rag_retrieval**
     Total Duration: 1800ms
     Average Duration: 1800.0ms
     Max Duration: 1800ms
     Number of Calls: 1

  📍 **llm_call**
     Total Duration: 600ms

## ⚠️  ABNORMAL SPAN IDENTIFIED
  Span Name: **rag_retrieval**
  Duration: 1800ms (72.0% of total)
  Max Duration: 1800ms
  → This span is taking abnormally long!

## 6. Log Analysis — Correlation ID & Root Cause
Correlation ID: **req-03c236aa**
Target Span: **rag_retrieval**

Found 2 related log entries:
  [response_sent]
    Timestamp: 2026-08-11T14:35:22.500Z
    Duration: 1800ms
    Message: RAG query took 1.8s, expected < 500ms

## 7. Root Cause Summary
🔴 **PRIMARY CAUSE:** The `rag_retrieval` span is experiencing abnormally high latency
   - Expected behavior: < 500ms
   - Observed behavior: 1800ms
   - Impact: Causes P95 latency to exceed threshold

## 8. Recommended Actions
**Immediate Fix:**
  - Optimize the abnormal span (e.g., RAG retrieval, LLM call)
  - Consider caching, query optimization, or resource scaling

**Preventive Measures:**
  - Set up alerting on P95 latency threshold
  - Implement distributed tracing monitoring
  - Create SLO/SLA with latency budget
  - Regular load testing to catch performance regressions
```

**Khi nào dùng:**
- **Sau khi chạy challenge** → chạy script này ngay lập tức
- **Để tạo báo cáo nhanh** → đã có tất cả phần cần trong `submission/evidence/`
- **Để nộp bài** → copy content vào `submission/REPORT.md`

---

## 🎯 Workflow CP3 Với 3 Script

### Trước 2:30 — Chuẩn Bị
```bash
# 1. Chạy baseline load test
python scripts/load_test.py --concurrency 5

# 2. Luyện tập với practice incident
python scripts/inject_incident.py --scenario rag_slow
python scripts/load_test.py --concurrency 5

# 3. Thử lọc log (quen lệnh)
python scripts/investigate_incident.py --feature refund --threshold 2000
```

### Đúng 2:30 — Khi Challenge Release
```bash
# 1. Chạy incident chính thức
python scripts/inject_incident.py
python scripts/load_test.py --challenge --concurrency 5

# 2. Tóm tắt incident (script này sẽ lấy tất cả info cần)
python scripts/summarize_incident.py
# → Check output file: submission/evidence/cp3_incident_summary.md

# 3. Nếu muốn chi tiết hơn, dùng investigate_incident.py
python scripts/investigate_incident.py --feature refund --threshold 2000
```

### 3:15–3:25 — Hoàn Thiện Báo Cáo
```bash
# 1. Copy content từ cp3_incident_summary.md vào submission/REPORT.md
cat submission/evidence/cp3_incident_summary.md >> submission/REPORT.md

# 2. Nếu cần trace detail, mở Langfuse hoặc chạy:
python scripts/read_traces.py --trace-id <TRACE_ID_FROM_SUMMARY>

# 3. Kiểm tra lại validator
python scripts/validate_logs.py
python scripts/validate_dashboard.py
```

---

## 🔧 Troubleshooting

### Script báo "File not found"
- Check xem bạn đang ở folder gốc repo không
- `ls data/logs.jsonl` → nên thấy file

### Không có log entries
- Chạy load test trước: `python scripts/load_test.py --concurrency 5`
- Wait cho API hoàn tất, mới chạy script

### Langfuse không kết nối
- Check `.env`: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` đúng không?
- Script vẫn chạy được mà chỉ không lấy trace từ API
- Log và metrics vẫn có trong `data/logs.jsonl`

### Không tìm được slow span
- Có thể incident chưa kích hoạt đúng
- Check: `config/challenge.json` có `incident: "rag_slow"` không?
- Chạy lại: `python scripts/inject_incident.py` + load test

---

## 📝 Cách Dùng Output Cho Báo Cáo

**Từ `summarize_incident.py`:**
- ✅ Challenge Config → copy vào section 1 báo cáo
- ✅ Metrics → copy vào section 3 báo cáo
- ✅ Slowest requests → copy vào section 4 báo cáo
- ✅ Trace analysis → copy vào section 5 báo cáo
- ✅ Root cause → copy vào section 7 báo cáo
- ✅ Recommended actions → copy vào section 8 báo cáo

**Từ `investigate_incident.py` + `read_traces.py`:**
- Lấy correlation ID → evidence
- Lấy span detail → evidence
- Lấy log lines → evidence
- Lấy trace waterfall → evidence

---

## ✅ Checklist Sử Dụng

- [ ] Trước 2:30: Chạy load test + practice incident + quen script
- [ ] 2:30: Chạy challenge incident + `summarize_incident.py`
- [ ] 3:00: Check kết quả, xác định root cause
- [ ] 3:15: Copy summary vào `submission/REPORT.md`
- [ ] 3:30: Validator pass, commit & push

**Mục tiêu:** Với 3 script này, bạn có thể điều tra incident trong 30 phút thay vì gỡ rối theo cách thủ công! 🚀
