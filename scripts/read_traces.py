#!/usr/bin/env python3
"""
Langfuse Trace Reader — Extract & summarize traces for CP3 investigation
Đọc trace từ Langfuse API hoặc local cache
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict

# Langfuse import (optional, will work without it)
try:
    from langfuse import Langfuse
    HAS_LANGFUSE = True
except ImportError:
    HAS_LANGFUSE = False


def get_trace_from_api(trace_id: str, langfuse_client=None) -> Optional[Dict]:
    """Lấy trace từ Langfuse API"""
    if not HAS_LANGFUSE or not langfuse_client:
        return None
    
    try:
        # Gọi Langfuse API
        trace = langfuse_client.get_trace(trace_id)
        return trace
    except Exception as e:
        print(f"❌ Error fetching trace from Langfuse: {e}")
        return None


def extract_slow_spans(trace: Dict, threshold_ms: int = 500) -> List[Dict]:
    """Trích xuất span chậm từ trace"""
    slow_spans = []
    
    if "spans" not in trace:
        return slow_spans
    
    for span in trace.get("spans", []):
        start_time = span.get("startTime")
        end_time = span.get("endTime")
        
        if start_time and end_time:
            try:
                start = datetime.fromisoformat(str(start_time).replace('Z', '+00:00'))
                end = datetime.fromisoformat(str(end_time).replace('Z', '+00:00'))
                duration_ms = (end - start).total_seconds() * 1000
                
                if duration_ms > threshold_ms:
                    slow_spans.append({
                        "name": span.get("name"),
                        "duration_ms": duration_ms,
                        "start_time": start_time,
                        "end_time": end_time,
                        "status": span.get("status"),
                        "metadata": span.get("metadata", {}),
                    })
            except Exception:
                continue
    
    return sorted(slow_spans, key=lambda x: x["duration_ms"], reverse=True)


def format_trace_waterfall(trace: Dict, max_depth: int = 10) -> str:
    """Định dạng trace dạng waterfall (ASCII art)"""
    output = []
    output.append(f"\n📍 Trace ID: {trace.get('id')}")
    output.append(f"   Input: {trace.get('input', {})}")
    output.append(f"   Output: {trace.get('output', {})}")
    output.append(f"   Metadata: {trace.get('metadata', {})}\n")
    
    spans = sorted(trace.get("spans", []), key=lambda x: x.get("startTime", ""))
    
    if not spans:
        output.append("   (No spans)")
        return "\n".join(output)
    
    # Tính min start time để normalize
    start_times = [s.get("startTime") for s in spans if s.get("startTime")]
    if start_times:
        min_start = min(start_times)
    else:
        min_start = None
    
    for i, span in enumerate(spans[:max_depth]):
        name = span.get("name", "unknown")
        start = span.get("startTime")
        end = span.get("endTime")
        status = span.get("status", "unknown")
        
        # Tính offset từ start
        offset_str = ""
        if start and min_start:
            try:
                start_dt = datetime.fromisoformat(str(start).replace('Z', '+00:00'))
                min_dt = datetime.fromisoformat(str(min_start).replace('Z', '+00:00'))
                offset_ms = (start_dt - min_dt).total_seconds() * 1000
                offset_str = f" [+{offset_ms:.0f}ms]"
            except Exception:
                pass
        
        # Tính duration
        duration_str = ""
        if start and end:
            try:
                start_dt = datetime.fromisoformat(str(start).replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(str(end).replace('Z', '+00:00'))
                duration_ms = (end_dt - start_dt).total_seconds() * 1000
                duration_str = f" {duration_ms:.0f}ms"
            except Exception:
                pass
        
        # Status icon
        icon = "✅" if status == "success" else "❌" if status == "error" else "⏳"
        
        # Indent based on nesting (simplified)
        indent = "  " * (i % 3)
        
        output.append(f"{indent}{icon} {name}{offset_str}{duration_str}")
        
        # Thêm metadata nếu có
        if span.get("metadata"):
            metadata_str = json.dumps(span.get("metadata"), indent=2)
            for line in metadata_str.split('\n'):
                output.append(f"{indent}   {line}")
    
    if len(spans) > max_depth:
        output.append(f"\n   ... ({len(spans) - max_depth} more spans)")
    
    return "\n".join(output)


def init_langfuse_client():
    """Khởi tạo Langfuse client từ .env"""
    if not HAS_LANGFUSE:
        print("⚠️  Langfuse library not installed. Run: pip install langfuse")
        return None
    
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    if not public_key or not secret_key:
        print("⚠️  LANGFUSE_PUBLIC_KEY or LANGFUSE_SECRET_KEY not set in .env")
        return None
    
    try:
        client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
        )
        print(f"✅ Connected to Langfuse at {host}")
        return client
    except Exception as e:
        print(f"❌ Failed to connect to Langfuse: {e}")
        return None


def get_traces_by_feature(langfuse_client, feature: str, limit: int = 10) -> List[Dict]:
    """Lấy traces theo feature"""
    if not langfuse_client:
        return []
    
    try:
        # Gọi API (thay đổi theo cấu trúc Langfuse của bạn)
        traces = []
        # Note: Cần điều chỉnh theo Langfuse API version
        print(f"ℹ️  Fetching traces for feature '{feature}' (limit: {limit})...")
        return traces
    except Exception as e:
        print(f"❌ Error fetching traces: {e}")
        return []


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python scripts/read_traces.py --trace-id <id>")
        print("  python scripts/read_traces.py --feature <feature> [--limit 10]")
        print("  python scripts/read_traces.py --slowest [--feature <feature>]")
        print("\nExamples:")
        print("  python scripts/read_traces.py --trace-id abc123xyz")
        print("  python scripts/read_traces.py --feature refund --limit 5")
        sys.exit(1)
    
    langfuse_client = init_langfuse_client()
    
    if "--trace-id" in sys.argv:
        trace_id_idx = sys.argv.index("--trace-id")
        trace_id = sys.argv[trace_id_idx + 1] if trace_id_idx + 1 < len(sys.argv) else None
        
        if not trace_id:
            print("❌ Please provide trace ID")
            sys.exit(1)
        
        trace = get_trace_from_api(trace_id, langfuse_client)
        
        if trace:
            print("\n" + "="*80)
            print("📊 TRACE WATERFALL".center(80))
            print("="*80)
            print(format_trace_waterfall(trace))
            
            print("\n" + "="*80)
            print("🔍 SLOW SPANS ANALYSIS".center(80))
            print("="*80)
            
            slow_spans = extract_slow_spans(trace, threshold_ms=500)
            if slow_spans:
                print(f"\nFound {len(slow_spans)} slow span(s):\n")
                for i, span in enumerate(slow_spans, 1):
                    print(f"  {i}. {span['name']}")
                    print(f"     Duration: {span['duration_ms']:.0f}ms ⚠️")
                    print(f"     Status: {span['status']}")
                    if span['metadata']:
                        print(f"     Metadata: {json.dumps(span['metadata'], indent=2)}")
                    print()
            else:
                print("✅ No slow spans found")
        else:
            print(f"❌ Could not fetch trace {trace_id}")
    
    elif "--feature" in sys.argv:
        feature_idx = sys.argv.index("--feature")
        feature = sys.argv[feature_idx + 1] if feature_idx + 1 < len(sys.argv) else "refund"
        
        limit = 10
        if "--limit" in sys.argv:
            limit_idx = sys.argv.index("--limit")
            limit = int(sys.argv[limit_idx + 1]) if limit_idx + 1 < len(sys.argv) else 10
        
        traces = get_traces_by_feature(langfuse_client, feature, limit)
        
        if traces:
            print(f"\n📊 Top {len(traces)} traces for feature '{feature}':\n")
            for i, trace in enumerate(traces, 1):
                print(f"  {i}. Trace ID: {trace.get('id')}")
                print(f"     Latency: {trace.get('latency_ms')}ms")
                print()
        else:
            print(f"ℹ️  No traces found for feature '{feature}'")


if __name__ == "__main__":
    main()
