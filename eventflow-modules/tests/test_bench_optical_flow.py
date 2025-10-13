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

def _python_shift_delay_fuse_ref(path: str, width: int, height: int, window_us: int, delay_us: int, edge_delay_us: int, min_count: int):
    from collections import deque, defaultdict
    eff_delay = int(delay_us + edge_delay_us)
    header = None
    a_events = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            ev = json.loads(line)
            if "header" in ev:
                header = ev["header"]
                continue
            ts = int(ev["ts"])
            x, y, pol = ev["idx"]
            if 0 <= x < width and 0 <= y < height and 0 <= pol <= 1:
                a_events.append({"ts": ts, "idx": [x, y, pol], "val": float(ev.get("val", 1.0))})
    a_events.sort(key=lambda e: e["ts"])

    # Build B streams by shifting ±1 in x and delaying
    a_map = defaultdict(list)
    b_map = defaultdict(list)
    for e in a_events:
        ts = e["ts"]; x, y, pol = e["idx"]
        a_map[(x, y, pol)].append(ts)
        b_ts = ts + eff_delay
        if x + 1 < width:
            b_map[(x + 1, y, pol)].append(b_ts)
        if x - 1 >= 0:
            b_map[(x - 1, y, pol)].append(b_ts)

    # Fuse per coordinate
    out = []
    keys = set(list(a_map.keys()) + list(b_map.keys()))
    for key in keys:
        va = sorted(a_map.get(key, []))
        vb = sorted(b_map.get(key, []))
        i = j = 0
        buf_a, buf_b = deque(), deque()
        while i < len(va) or j < len(vb):
            take_a = j >= len(vb) or (i < len(va) and va[i] <= vb[j])
            if take_a:
                t = va[i]; i += 1; buf_a.append(t)
            else:
                t = vb[j]; j += 1; buf_b.append(t)
            cutoff = t - window_us
            while buf_a and buf_a[0] < cutoff: buf_a.popleft()
            while buf_b and buf_b[0] < cutoff: buf_b.popleft()
            if buf_a and buf_b and (len(buf_a) + len(buf_b)) >= min_count:
                x, y, pol = key
                out.append({"ts": t, "idx": [x, y, pol], "val": 1.0})
    out.sort(key=lambda e: (e["ts"], e["idx"][0], e["idx"][1], e["idx"][2]))
    if header is None:
        header = {"dims": ["x", "y", "polarity"], "layout": "coo"}
    return header, out

def test_optical_flow_shift_delay_fuse_parity():
    path = _get_vision_trace_path()
    width = 128; height = 128
    window_us = 5000; delay_us = 2000; edge_delay_us = 200; min_count = 2

    # Python reference
    _, py_events = _python_shift_delay_fuse_ref(path, width, height, window_us, delay_us, edge_delay_us, min_count)

    # Native
    if mod_native is None or not hasattr(mod_native, "optical_flow_shift_delay_fuse_coo"):
        pytest.skip("Native optical_flow_shift_delay_fuse_coo not available")
    _, rs_events = mod_native.optical_flow_shift_delay_fuse_coo(path, width, height, window_us, delay_us, edge_delay_us, min_count)

    py_events.sort(key=lambda x: (x["ts"], x["idx"][0], x["idx"][1], x["idx"][2]))
    rs_events.sort(key=lambda x: (x["ts"], x["idx"][0], x["idx"][1], x["idx"][2]))
    assert rs_events == py_events, "Rust shift/delay/fuse output must match Python reference"


@pytest.mark.parametrize("impl", ["native", "python"])
def test_bench_optical_flow_shift_delay_fuse(benchmark, impl: str):
    path = _get_vision_trace_path()
    width = 128
    height = 128
    window_us = 5000
    delay_us = 2000
    edge_delay_us = 200
    min_count = 2

    if impl == "native":
        if mod_native is None or not hasattr(mod_native, "optical_flow_shift_delay_fuse_coo"):
            pytest.skip("Native optical_flow_shift_delay_fuse_coo not available")
        def run():
            return mod_native.optical_flow_shift_delay_fuse_coo(
                path, width, height, window_us, delay_us, edge_delay_us, min_count
            )
    else:
        def run():
            # Python reference for shift/delay/fuse
            return _python_shift_delay_fuse_ref(
                path, width, height, window_us, delay_us, edge_delay_us, min_count
            )

    header, events = benchmark(run)
    assert isinstance(header, dict)
    assert isinstance(events, list)

@pytest.mark.parametrize("impl", ["native", "python"])
def test_bench_optical_flow_arrays(benchmark, impl: str):
    path = _get_vision_trace_path()
    width = 128
    height = 128
    window_us = 5000
    delay_us = 2000
    edge_delay_us = 200
    min_count = 2

    if impl == "native":
        if mod_native is None or not hasattr(mod_native, "optical_flow_shift_delay_fuse_arrays"):
            pytest.skip("Native optical_flow_shift_delay_fuse_arrays not available")
        def run():
            return mod_native.optical_flow_shift_delay_fuse_arrays(
                path, width, height, window_us, delay_us, edge_delay_us, min_count
            )
    else:
        def run():
            # Python fallback arrays baseline: use reference COO then convert to columns
            hdr, events = _python_shift_delay_fuse_ref(
                path, width, height, window_us, delay_us, edge_delay_us, min_count
            )
            n = len(events)
            ts = np.fromiter((e["ts"] for e in events), dtype=np.int64, count=n)
            x = np.fromiter((e["idx"][0] for e in events), dtype=np.int64, count=n)
            y = np.fromiter((e["idx"][1] for e in events), dtype=np.int64, count=n)
            pol = np.fromiter((e["idx"][2] for e in events), dtype=np.int64, count=n)
            val = np.full((n,), 1.0, dtype=np.float32)
            arrays = {"ts": ts, "x": x, "y": y, "polarity": pol, "val": val}
            return hdr, arrays

    header, arrays = benchmark(run)
    assert isinstance(header, dict)
    assert isinstance(arrays, dict)
    assert set(arrays.keys()) == {"ts", "x", "y", "polarity", "val"}
    n = len(arrays["ts"])
    assert arrays["x"].shape == arrays["y"].shape == arrays["polarity"].shape == arrays["val"].shape == arrays["ts"].shape
    assert arrays["ts"].dtype == np.int64
    assert arrays["x"].dtype == np.int64
    assert arrays["y"].dtype == np.int64
    assert arrays["polarity"].dtype == np.int64
    assert arrays["val"].dtype == np.float32


@pytest.mark.parametrize("impl", ["native", "python"])
def test_bench_optical_flow_coo_arrays(benchmark, impl: str):
    path = _get_vision_trace_path()
    width = 128
    height = 128

    # Compare wrapper-based arrays path: native vs Python fallback via EF_NATIVE
    if impl == "native":
        os.environ["EF_NATIVE"] = "1"
    else:
        os.environ["EF_NATIVE"] = "0"

    from eventflow_modules.vision.optical_flow import load_events_from_jsonl

    def run():
        return load_events_from_jsonl(path, width, height, as_arrays=True)

    header, arrays = benchmark(run)
    assert isinstance(header, dict)
    assert isinstance(arrays, dict)
    assert set(arrays.keys()) == {"ts", "x", "y", "polarity", "val"}
    n = len(arrays["ts"])
    assert arrays["x"].shape == arrays["y"].shape == arrays["polarity"].shape == arrays["val"].shape == arrays["ts"].shape
    assert arrays["ts"].dtype == np.int64
    assert arrays["x"].dtype == np.int64
    assert arrays["y"].dtype == np.int64
    assert arrays["polarity"].dtype == np.int64
    assert arrays["val"].dtype == np.float32
