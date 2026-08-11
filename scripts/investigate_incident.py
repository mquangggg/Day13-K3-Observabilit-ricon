#!/usr/bin/env python3
"""
Incident Investigation Helper — CP3 Challenge
Điều tra incident: lọc log, tìm trace, xác định root cause
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

def load_logs(log_file: str = "data/logs.jsonl") -> list:
    """Đọc tất cả log từ JSONL file"""
    logs = []
    log_path = Path(log_file)
    
    if not log_path.exists():
        print(f"❌ File {log_file} không tồn tại")
        return logs
    
    with open(log_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                log_entry = json.loads(line.strip())
                logs.append(log_entry)
            except json.JSONDecodeError as e:
                print(f"⚠️  Line {line_num}: JSON decode error: {e}")
                continue
    
    return logs


def filter_logs_by_correlation_id(logs: list, correlation_id: str) -> list:
    """Lọc log theo correlation ID"""
    return [log for log in logs if log.get("correlation_id") == correlation_id]


def filter_logs_by_feature(logs: list, feature: str) -> list:
    """Lọc log theo feature"""
    return [log for log in logs if log.get("feature") == feature]


def filter_logs_by_event(logs: list, event: str) -> list:
    """Lọc log theo event type"""
    return [log for log in logs if log.get("event") == event]


def get_logs_by_time_range(logs: list, start_time: datetime, end_time: datetime) -> list:
    """Lọc log theo time range (nếu có timestamp)"""
    filtered = []
    for log in logs:
        if "timestamp" in log:
            try:
                log_time = datetime.fromisoformat(log["timestamp"].replace('Z', '+00:00'))
                if start_time <= log_time <= end_time:
                    filtered.append(log)
            except Exception:
                continue
    return filtered


def identify_slow_requests(logs: list, threshold_ms: int = 2000) -> list:
    """Tìm request chậm (latency > threshold)"""
    slow_requests = []
    
    for log in logs:
        if log.get("event") == "response_sent":
            latency = log.get("latency_ms", 0)
            if latency > threshold_ms:
                slow_requests.append({
                    "correlation_id": log.get("correlation_id"),
                    "latency_ms": latency,
                    "feature": log.get("feature"),
                    "timestamp": log.get("timestamp"),
                    "user_id_hash": log.get("user_id_hash"),
                })
    
    return sorted(slow_requests, key=lambda x: x["latency_ms"], reverse=True)


def identify_failed_requests(logs: list) -> list:
    """Tìm request bị lỗi"""
    failed = []
    
    for log in logs:
        if log.get("event") == "request_failed":
            failed.append({
                "correlation_id": log.get("correlation_id"),
                "error_type": log.get("error_type"),
                "error_message": log.get("error_message"),
                "feature": log.get("feature"),
                "timestamp": log.get("timestamp"),
                "span_name": log.get("span_name"),
            })
    
    return failed


def analyze_span_latencies(logs: list, correlation_id: str) -> dict:
    """Phân tích latency từng span trong một request"""
    request_logs = filter_logs_by_correlation_id(logs, correlation_id)
    
    spans = defaultdict(list)
    for log in request_logs:
        if "span_name" in log and "duration_ms" in log:
            spans[log["span_name"]].append({
                "duration_ms": log["duration_ms"],
                "event": log.get("event"),
                "timestamp": log.get("timestamp"),
            })
    
    # Tính tổng time mỗi span
    span_summary = {}
    for span_name, span_logs in spans.items():
        total_time = sum(s["duration_ms"] for s in span_logs)
        span_summary[span_name] = {
            "total_ms": total_time,
            "calls": len(span_logs),
            "avg_ms": total_time / len(span_logs) if span_logs else 0,
            "max_ms": max(s["duration_ms"] for s in span_logs) if span_logs else 0,
        }
    
    return dict(sorted(span_summary.items(), key=lambda x: x[1]["total_ms"], reverse=True))


def print_investigation_report(logs: list, feature: str, latency_threshold: int = 2000):
    """In báo cáo điều tra"""
    
    print("\n" + "="*80)
    print("📊 INCIDENT INVESTIGATION REPORT".center(80))
    print("="*80 + "\n")
    
    # 1. Tìm slow requests
    print(f"🔍 **Step 1: Slow Requests** (latency > {latency_threshold}ms)")
    print("-" * 80)
    
    feature_logs = filter_logs_by_feature(logs, feature)
    slow_requests = identify_slow_requests(feature_logs, latency_threshold)
    
    if slow_requests:
        print(f"Found {len(slow_requests)} slow request(s) in feature '{feature}':\n")
        for i, req in enumerate(slow_requests[:5], 1):  # Show top 5
            print(f"  {i}. Correlation ID: {req['correlation_id']}")
            print(f"     Latency: {req['latency_ms']}ms ⚠️")
            print(f"     Feature: {req['feature']}")
            print(f"     User: {req['user_id_hash']}")
            print(f"     Time: {req['timestamp']}\n")
    else:
        print(f"✅ No slow requests found in feature '{feature}'\n")
    
    # 2. Phân tích span chậm nhất
    if slow_requests:
        slowest_id = slow_requests[0]["correlation_id"]
        print(f"\n🔍 **Step 2: Span Analysis** (Correlation ID: {slowest_id})")
        print("-" * 80)
        
        span_latencies = analyze_span_latencies(logs, slowest_id)
        
        if span_latencies:
            print(f"Span breakdown for slowest request:\n")
            for span_name, metrics in span_latencies.items():
                print(f"  📍 {span_name}")
                print(f"     Total: {metrics['total_ms']}ms | Avg: {metrics['avg_ms']:.1f}ms | Max: {metrics['max_ms']}ms | Calls: {metrics['calls']}")
                if metrics['total_ms'] > latency_threshold * 0.8:
                    print(f"     ⚠️  THIS SPAN IS ABNORMAL!")
                print()
        
        # 3. In logs của request chậm nhất
        print(f"\n🔍 **Step 3: Detailed Logs** (Correlation ID: {slowest_id})")
        print("-" * 80)
        
        request_logs = filter_logs_by_correlation_id(logs, slowest_id)
        if request_logs:
            print(f"Total {len(request_logs)} log entries for this request:\n")
            for log_entry in sorted(request_logs, key=lambda x: x.get("timestamp", "")):
                event = log_entry.get("event", "unknown")
                span = log_entry.get("span_name", "-")
                duration = log_entry.get("duration_ms", "-")
                message = log_entry.get("message", "")
                
                print(f"  [{event}] {span}")
                if duration != "-":
                    print(f"     Duration: {duration}ms")
                if message:
                    print(f"     Message: {message}")
                print()
    
    # 4. Failed requests
    print(f"\n🔍 **Step 4: Failed Requests**")
    print("-" * 80)
    
    failed = identify_failed_requests(feature_logs)
    if failed:
        print(f"Found {len(failed)} failed request(s):\n")
        for i, req in enumerate(failed[:5], 1):
            print(f"  {i}. Correlation ID: {req['correlation_id']}")
            print(f"     Error Type: {req['error_type']}")
            print(f"     Error Message: {req['error_message']}")
            print(f"     Span: {req['span_name']}")
            print()
    else:
        print("✅ No failed requests\n")
    
    print("="*80 + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/investigate_incident.py --feature <feature_name> [--threshold <ms>]")
        print("  python scripts/investigate_incident.py --correlation-id <id>")
        print("  python scripts/investigate_incident.py --slow [--threshold <ms>]")
        print("\nExamples:")
        print("  python scripts/investigate_incident.py --feature refund --threshold 2000")
        print("  python scripts/investigate_incident.py --correlation-id req-03c236aa")
        print("  python scripts/investigate_incident.py --slow")
        sys.exit(1)
    
    logs = load_logs("data/logs.jsonl")
    print(f"✅ Loaded {len(logs)} log entries\n")
    
    if "--feature" in sys.argv:
        feature_idx = sys.argv.index("--feature")
        feature = sys.argv[feature_idx + 1] if feature_idx + 1 < len(sys.argv) else "refund"
        
        threshold = 2000
        if "--threshold" in sys.argv:
            threshold_idx = sys.argv.index("--threshold")
            threshold = int(sys.argv[threshold_idx + 1]) if threshold_idx + 1 < len(sys.argv) else 2000
        
        print_investigation_report(logs, feature, threshold)
    
    elif "--correlation-id" in sys.argv:
        corr_idx = sys.argv.index("--correlation-id")
        correlation_id = sys.argv[corr_idx + 1] if corr_idx + 1 < len(sys.argv) else None
        
        if not correlation_id:
            print("❌ Please provide correlation ID")
            sys.exit(1)
        
        print(f"\n🔍 Logs for Correlation ID: {correlation_id}")
        print("="*80 + "\n")
        
        request_logs = filter_logs_by_correlation_id(logs, correlation_id)
        span_latencies = analyze_span_latencies(logs, correlation_id)
        
        if request_logs:
            print(f"Found {len(request_logs)} log entries:\n")
            for log_entry in sorted(request_logs, key=lambda x: x.get("timestamp", "")):
                print(json.dumps(log_entry, indent=2))
                print()
            
            print(f"\n📊 Span Latency Summary:")
            print("-"*80)
            for span_name, metrics in span_latencies.items():
                print(f"  {span_name}: {metrics['total_ms']}ms (avg: {metrics['avg_ms']:.1f}ms, max: {metrics['max_ms']}ms)")
        else:
            print(f"❌ No logs found for correlation ID: {correlation_id}")
    
    elif "--slow" in sys.argv:
        threshold = 2000
        if "--threshold" in sys.argv:
            threshold_idx = sys.argv.index("--threshold")
            threshold = int(sys.argv[threshold_idx + 1]) if threshold_idx + 1 < len(sys.argv) else 2000
        
        print_investigation_report(logs, "refund", threshold)


if __name__ == "__main__":
    main()
