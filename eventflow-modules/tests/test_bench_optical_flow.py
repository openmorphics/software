from __future__ import annotations
import numpy as np
import pytest
import json
import os

try:
    from eventflow_modules._rust import native as mod_native
except Exception:
    mod_native = None  # type: ignore


@pytest.mark.parametrize("impl", ["native", "python"])
def test_bench_optical_flow_stub(benchmark, impl: str):
    H, W = 1024, 1024
    rng = np.random.default_rng(20240930)
    arr = rng.random((H, W), dtype=np.float32)

    if impl == "native":
        if mod_native is None or not hasattr(mod_native, "optical_flow_stub"):
            pytest.skip("Native optical_flow_stub not available")
        def run():
            return mod_native.optical_flow_stub(arr)
    else:
        def run():
            # Approximate similar memory traffic baseline
            return arr.copy()

    out = benchmark(run)
    out = np.asarray(out, dtype=np.float32)
    assert out.shape == (H, W)
    assert out.dtype == np.float32

def _get_vision_trace_path():
    # CWD is repo root, so path is relative to that.
    path = "examples/vision_optical_flow/traces/inputs/vision.norm.jsonl"
    if not os.path.exists(path):
        pytest.skip(f"Test trace not found at {os.path.abspath(path)}")
    return path

def python_coo_from_jsonl_ref(path: str, width, height, window_us, delay_us, edge_delay_us, min_count):
    from collections import deque
    
    # These parameters are from the eir.json
    eff_delay = delay_us + edge_delay_us

    # A-stream is the original event stream
    # B-stream is the shifted and delayed stream
    a_stream = []
    header = None
    with open(path, 'r') as f:
        for line in f:
            if not line.strip(): continue
            ev = json.loads(line)
            if "header" in ev:
                header = ev["header"]
            else:
                a_stream.append(ev)
    
    a_stream.sort(key=lambda e: e['ts'])
    
    # Create the two B-streams by shifting and delaying
    b_stream_east = [{"ts": e["ts"] + eff_delay, "idx": [e["idx"][0] - 1, e["idx"][1], e["idx"][2]], "val": e["val"]} for e in a_stream if e["idx"][0] > 0]
    b_stream_west = [{"ts": e["ts"] + eff_delay, "idx": [e["idx"][0] + 1, e["idx"][1], e["idx"][2]], "val": e["val"]} for e in a_stream if e["idx"][0] < width - 1]
    
    out_events = []
    
    def fuse_streams(s_a, s_b, win, minc):
        merged = sorted(
            [(e['ts'], 'a', e) for e in s_a] +
            [(e['ts'], 'b', e) for e in s_b],
            key=lambda x: x[0]
        )
        
        buf_a = deque()
        buf_b = deque()
        fused = []
        
        for t, stream_id, event in merged:
            cutoff = t - win
            
            while buf_a and buf_a[0]['ts'] < cutoff: buf_a.popleft()
            while buf_b and buf_b[0]['ts'] < cutoff: buf_b.popleft()

            if stream_id == 'a':
                buf_a.append(event)
            else:
                buf_b.append(event)
            
            if buf_a and buf_b and (len(buf_a) + len(buf_b)) >= minc:
                # Use the current event's full dict to represent the fused event
                fused.append(event)
        
        return fused

    out_events.extend(fuse_streams(a_stream, b_stream_east, window_us, min_count))
    out_events.extend(fuse_streams(a_stream, b_stream_west, window_us, min_count))

    # Deduplicate and format
    unique_events = {(e['ts'], tuple(e['idx']), e['val']) for e in out_events}
    sorted_events = sorted(list(unique_events), key=lambda x: (x[0], x[1]))
    final_events = [{"ts": ts, "idx": list(idx), "val": val} for ts, idx, val in sorted_events]
    
    return header, final_events

@pytest.mark.parametrize("impl", ["native", "python"])
def test_bench_optical_flow_coo_from_jsonl(benchmark, impl):
    path = _get_vision_trace_path()
    if impl == "native":
        if mod_native is None or not hasattr(mod_native, "optical_flow_coo_from_jsonl"):
            pytest.skip("Native optical_flow_coo_from_jsonl not available")
        def run():
            return mod_native.optical_flow_coo_from_jsonl(path, 128, 128, 5000, 2000, 200, 1)
    else:
        def run():
            # Pure python reference implementation
            return python_coo_from_jsonl_ref(path, 128, 128, 5000, 2000, 200, 1)
    
    header, events = benchmark(run)
    assert isinstance(header, dict)
    assert isinstance(events, list)
    assert "dims" in header and "layout" in header
    if events:
        assert isinstance(events[0], dict)
        assert "ts" in events[0] and "idx" in events[0]

def _load_golden_trace():
    path = "examples/vision_optical_flow/traces/golden/vision.golden.jsonl"
    if not os.path.exists(path):
        pytest.skip(f"Golden trace not found at {os.path.abspath(path)}")
    
    events = []
    with open(path, 'r') as f:
        for line in f:
            if not line.strip(): continue
            ev = json.loads(line)
            if "header" in ev: continue
            events.append(ev)
    return events


def test_optical_flow_coo_parity():
    path = _get_vision_trace_path()
    
    # Get python reference events
    _, python_events = python_coo_from_jsonl_ref(path, 128, 128, 5000, 2000, 200, 1)
    
    # Get native events
    if mod_native is None or not hasattr(mod_native, "optical_flow_coo_from_jsonl"):
        pytest.skip("Native optical_flow_coo_from_jsonl not available")
    _, native_events = mod_native.optical_flow_coo_from_jsonl(path, 128, 128, 5000, 2000, 200, 1)
    
    # Get golden events
    golden_events = _load_golden_trace()

    # Sort all events for consistent comparison
    python_events.sort(key=lambda x: (x['ts'], x['idx'][0], x['idx'][1], x['idx'][2]))
    native_events.sort(key=lambda x: (x['ts'], x['idx'][0], x['idx'][1], x['idx'][2]))
    golden_events.sort(key=lambda x: (x['ts'], x['idx'][0], x['idx'][1], x['idx'][2]))

    assert python_events == golden_events, "Python reference implementation does not match golden trace"
    assert native_events == golden_events, "Native Rust implementation does not match golden trace"
