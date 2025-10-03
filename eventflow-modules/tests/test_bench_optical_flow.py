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
    # For this example graph, the "flow" probe captures the kernel output directly,
    # which is a pass-through of normalized events. Return input events bounded to dims.
    header = None
    events = []
    with open(path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            ev = json.loads(line)
            if "header" in ev:
                header = ev["header"]
                continue
            ts = ev.get("ts")
            idx = ev.get("idx", [])
            if not isinstance(idx, list) or len(idx) != 3:
                continue
            x, y, pol = idx
            if 0 <= x < width and 0 <= y < height and 0 <= pol <= 1:
                val = ev.get("val", 1.0)
                events.append({"ts": ts, "idx": [x, y, pol], "val": float(val)})
    events.sort(key=lambda e: (e["ts"], e["idx"][0], e["idx"][1], e["idx"][2]))
    if header is None:
        header = {"dims": ["x", "y", "polarity"], "layout": "coo"}
    return header, events

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
