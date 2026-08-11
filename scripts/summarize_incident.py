#!/usr/bin/env python3
"""
CP3 Incident Summarizer — Nối Metrics → Traces → Logs → Root Cause
Tóm tắt báo cáo điều tra challenge chính thức
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def load_challenge_config(config_file: str = "config/challenge.json") -> dict:
    """Đọc challenge config"""
    config_path = Path(config_file)
    
    if not config_path.exists():
        print(f"❌ File {config_file} không tồn tại")
        return {}
    
    with open(config_path, 'r') as f:
        return json.load(f)


def load_logs(log_file: str = "data/logs.jsonl") -> list:
    """Đọc logs"""
    logs = []
    log_path = Path(log_file)
    
    if not log_path.exists():
        return logs
    
    with open(log_path, 'r') as f:
        for line in f:
            try:
                logs.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    
    return logs


def get_incident_metrics(logs: list, feature: str, latency_threshold: int = 2000) -> dict:
    """Tính toán metrics của incident"""
    feature_logs = [log for log in logs if log.get("feature") == feature]
    
    latencies = []
    error_count = 0
    error_types = defaultdict(int)
    total_requests = 0
    
    for log in feature_logs:
        if log.get("event") == "response_sent":
            total_requests += 1
            latency = log.get("latency_ms", 0)
            latencies.append(latency)
        
        if log.get("event") == "request_failed":
            error_count += 1
            error_type = log.get("error_type", "unknown")
            error_types[error_type] += 1
    
    if not latencies:
        return {}
    
    latencies_sorted = sorted(latencies)
    p50 = latencies_sorted[len(latencies_sorted) // 2]
    p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)]
    p99 = latencies_sorted[int(len(latencies_sorted) * 0.99)]
    
    return {
        "feature": feature,
        "total_requests": total_requests,
        "latency_p50_ms": p50,
        "latency_p95_ms": p95,
        "latency_p99_ms": p99,
        "latency_threshold_ms": latency_threshold,
        "error_count": error_count,
        "error_rate_pct": (error_count / total_requests * 100) if total_requests else 0,
        "error_types": dict(error_types),
        "p95_exceeds_threshold": p95 > latency_threshold,
    }


def identify_symptoms(metrics: dict) -> list:
    """Xác định triệu chứng từ metrics"""
    symptoms = []
    
    if metrics.get("p95_exceeds_threshold"):
        symptoms.append(f"⚠️  P95 latency ({metrics['latency_p95_ms']}ms) exceeds threshold ({metrics['latency_threshold_ms']}ms)")
    
    if metrics.get("error_rate_pct", 0) > 0:
        symptoms.append(f"⚠️  Error rate: {metrics['error_rate_pct']:.1f}% ({metrics['error_count']} errors)")
    
    if metrics.get("error_types"):
        for error_type, count in metrics["error_types"].items():
            symptoms.append(f"   - {error_type}: {count} occurrences")
    
    return symptoms


def get_slowest_requests(logs: list, feature: str, limit: int = 3) -> list:
    """Lấy slowest requests"""
    slow_requests = []
    
    for log in logs:
        if log.get("event") == "response_sent" and log.get("feature") == feature:
            slow_requests.append({
                "correlation_id": log.get("correlation_id"),
                "latency_ms": log.get("latency_ms"),
                "timestamp": log.get("timestamp"),
                "user_id": log.get("user_id_hash"),
            })
    
    return sorted(slow_requests, key=lambda x: x["latency_ms"], reverse=True)[:limit]


def analyze_slow_request_spans(logs: list, correlation_id: str) -> dict:
    """Analisis span latency từ slowest request"""
    request_logs = [log for log in logs if log.get("correlation_id") == correlation_id]
    
    spans = defaultdict(list)
    for log in request_logs:
        if "span_name" in log and "duration_ms" in log:
            spans[log["span_name"]].append({
                "duration_ms": log["duration_ms"],
                "event": log.get("event"),
                "message": log.get("message", ""),
            })
    
    span_summary = {}
    for span_name, span_logs in spans.items():
        total_time = sum(s["duration_ms"] for s in span_logs)
        span_summary[span_name] = {
            "total_ms": total_time,
            "calls": len(span_logs),
            "avg_ms": total_time / len(span_logs) if span_logs else 0,
            "max_ms": max(s["duration_ms"] for s in span_logs) if span_logs else 0,
            "events": [s["event"] for s in span_logs],
        }
    
    # Sắp xếp theo total time
    return dict(sorted(span_summary.items(), key=lambda x: x[1]["total_ms"], reverse=True))


def identify_abnormal_span(span_summary: dict, threshold_factor: float = 0.5) -> tuple:
    """Tìm span bất thường (chiếm > 50% total time)"""
    total_time = sum(s["total_ms"] for s in span_summary.values())
    
    for span_name, metrics in span_summary.items():
        if metrics["total_ms"] > total_time * threshold_factor:
            return span_name, metrics
    
    # Nếu không có, trả về span lớn nhất
    if span_summary:
        first_span = list(span_summary.items())[0]
        return first_span[0], first_span[1]
    
    return None, None


def get_related_log_lines(logs: list, correlation_id: str, span_name: str) -> list:
    """Lấy log lines liên quan đến span"""
    related_logs = []
    
    for log in logs:
        if log.get("correlation_id") == correlation_id and log.get("span_name") == span_name:
            related_logs.append({
                "timestamp": log.get("timestamp"),
                "event": log.get("event"),
                "message": log.get("message", ""),
                "duration_ms": log.get("duration_ms"),
                "span_name": log.get("span_name"),
            })
    
    return sorted(related_logs, key=lambda x: x.get("timestamp", ""))


def generate_report(config: dict, metrics: dict, symptoms: list, 
                   slow_requests: list, abnormal_span: tuple, related_logs: list, logs: list) -> str:
    """Tạo báo cáo điều tra"""
    
    report = []
    report.append("\n" + "="*80)
    report.append("📋 INCIDENT INVESTIGATION REPORT — CP3 CHALLENGE".center(80))
    report.append("="*80 + "\n")
    
    # Section 1: Challenge Info
    report.append("## 1. Challenge Configuration\n")
    report.append(f"Challenge ID: {config.get('challenge_id')}")
    report.append(f"Incident Type: {config.get('incident')}")
    report.append(f"Affected Feature: {config.get('affected_feature')}")
    report.append(f"Latency Threshold: {config.get('latency_threshold_ms')}ms")
    report.append(f"Seed: {config.get('seed')}")
    report.append(f"Test Queries: {len(config.get('queries', []))} queries\n")
    
    # Section 2: Symptoms (from Metrics)
    report.append("## 2. Symptoms Detected (from Metrics)\n")
    
    if symptoms:
        for symptom in symptoms:
            report.append(f"  {symptom}")
    else:
        report.append("  ✅ No abnormalities detected")
    
    report.append("")
    
    # Section 3: Metrics Summary
    report.append("## 3. Metrics Summary\n")
    report.append(f"  Feature: {metrics.get('feature')}")
    report.append(f"  Total Requests: {metrics.get('total_requests')}")
    report.append(f"  P50 Latency: {metrics.get('latency_p50_ms')}ms")
    report.append(f"  P95 Latency: {metrics.get('latency_p95_ms')}ms ← **KEY METRIC**")
    report.append(f"  P99 Latency: {metrics.get('latency_p99_ms')}ms")
    report.append(f"  Threshold: {metrics.get('latency_threshold_ms')}ms")
    report.append(f"  Error Rate: {metrics.get('error_rate_pct', 0):.1f}%\n")
    
    # Section 4: Slowest Requests
    if slow_requests:
        report.append("## 4. Slowest Requests\n")
        for i, req in enumerate(slow_requests, 1):
            report.append(f"  {i}. Correlation ID: **{req['correlation_id']}**")
            report.append(f"     Latency: {req['latency_ms']}ms")
            report.append(f"     Timestamp: {req['timestamp']}\n")
    
    # Section 5: Trace Analysis (Span Breakdown)
    if slow_requests:
        report.append("## 5. Trace Analysis — Span Breakdown\n")
        report.append(f"(For slowest request: {slow_requests[0]['correlation_id']})\n")
        
        span_summary = analyze_slow_request_spans(logs, slow_requests[0]['correlation_id'])
        
        for span_name, metrics in span_summary.items():
            report.append(f"  📍 **{span_name}**")
            report.append(f"     Total Duration: {metrics['total_ms']}ms")
            report.append(f"     Average Duration: {metrics['avg_ms']:.1f}ms")
            report.append(f"     Max Duration: {metrics['max_ms']}ms")
            report.append(f"     Number of Calls: {metrics['calls']}\n")
        
        # Identify abnormal span
        abnormal_name, abnormal_metrics = identify_abnormal_span(span_summary)
        
        if abnormal_name:
            total_time = sum(s["total_ms"] for s in span_summary.values())
            percentage = (abnormal_metrics["total_ms"] / total_time * 100) if total_time else 0
            report.append(f"## ⚠️  ABNORMAL SPAN IDENTIFIED\n")
            report.append(f"  Span Name: **{abnormal_name}**")
            report.append(f"  Duration: {abnormal_metrics['total_ms']}ms ({percentage:.1f}% of total)")
            report.append(f"  Max Duration: {abnormal_metrics['max_ms']}ms")
            report.append(f"  → This span is taking abnormally long!\n")
    
    # Section 6: Log Analysis
    if slow_requests and abnormal_span[0]:
        report.append("## 6. Log Analysis — Correlation ID & Root Cause\n")
        
        corr_id = slow_requests[0]['correlation_id']
        span_name = abnormal_span[0]
        
        report.append(f"Correlation ID: **{corr_id}**")
        report.append(f"Target Span: **{span_name}**\n")
        
        related_logs = get_related_log_lines(logs, corr_id, span_name)
        
        if related_logs:
            report.append(f"Found {len(related_logs)} related log entries:\n")
            for log_entry in related_logs:
                report.append(f"  [{log_entry['event']}]")
                report.append(f"    Timestamp: {log_entry['timestamp']}")
                if log_entry['duration_ms']:
                    report.append(f"    Duration: {log_entry['duration_ms']}ms")
                if log_entry['message']:
                    report.append(f"    Message: {log_entry['message']}")
                report.append()
        else:
            report.append("  ℹ️  No related log entries found\n")
    
    # Section 7: Root Cause Summary
    report.append("## 7. Root Cause Summary\n")
    report.append("Based on Metrics → Traces → Logs:\n")
    
    if symptoms:
        if abnormal_span[0]:
            report.append(f"🔴 **PRIMARY CAUSE:** The `{abnormal_span[0]}` span is experiencing abnormally high latency")
            report.append(f"   - Expected behavior: < 500ms")
            report.append(f"   - Observed behavior: {abnormal_span[1]['total_ms']}ms")
            report.append(f"   - Impact: Causes P95 latency to exceed threshold\n")
        else:
            report.append("🔴 **PRIMARY CAUSE:** Overall high latency in request processing\n")
    else:
        report.append("✅ No root cause identified - incident may not be present\n")
    
    # Section 8: Recommended Actions
    report.append("## 8. Recommended Actions\n")
    report.append("**Immediate Fix:**")
    report.append("  - Optimize the abnormal span (e.g., RAG retrieval, LLM call)")
    report.append("  - Consider caching, query optimization, or resource scaling\n")
    report.append("**Preventive Measures:**")
    report.append("  - Set up alerting on P95 latency threshold")
    report.append("  - Implement distributed tracing monitoring")
    report.append("  - Create SLO/SLA with latency budget")
    report.append("  - Regular load testing to catch performance regressions\n")
    
    report.append("="*80 + "\n")
    
    return "\n".join(report)


def main():
    # Đọc config và logs
    config = load_challenge_config()
    if not config:
        print("❌ Cannot load challenge config")
        sys.exit(1)
    
    logs = load_logs()
    print(f"✅ Loaded {len(logs)} log entries\n")
    
    # Tính metrics
    feature = config.get("affected_feature", "refund")
    latency_threshold = config.get("latency_threshold_ms", 2000)
    
    metrics = get_incident_metrics(logs, feature, latency_threshold)
    if not metrics:
        print(f"❌ No metrics found for feature '{feature}'")
        sys.exit(1)
    
    # Xác định triệu chứng
    symptoms = identify_symptoms(metrics)
    
    # Lấy slow requests
    slow_requests = get_slowest_requests(logs, feature, limit=3)
    
    # Analyze slowest request
    abnormal_span = (None, None)
    related_logs = []
    
    if slow_requests:
        span_summary = analyze_slow_request_spans(logs, slow_requests[0]['correlation_id'])
        abnormal_span = identify_abnormal_span(span_summary)
        
        if abnormal_span[0]:
            related_logs = get_related_log_lines(logs, slow_requests[0]['correlation_id'], abnormal_span[0])
    
    # Tạo báo cáo
    report = generate_report(config, metrics, symptoms, slow_requests, abnormal_span, related_logs, logs)
    print(report)
    
    # Lưu báo cáo vào file
    output_file = "submission/evidence/cp3_incident_summary.md"
    Path("submission/evidence").mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ Report saved to {output_file}")


if __name__ == "__main__":
    main()
