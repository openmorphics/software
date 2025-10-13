from __future__ import annotations
import os
import time
import json
import statistics
from typing import Callable, Any
import numpy as np
import pytest

try:
    from eventflow_modules._rust import native as vis_native
except Exception:
    vis_native = None  # type: ignore


def _env_enabled(name: str) -> bool:
    val = os.getenv(name)
    if val is None:
        return False
    v = val.strip().lower()
    return v in ("1", "true", "on", "yes", "enable")


GATE_ENABLED = os.getenv("EF_BENCH_GATE") == "1"

pytestmark = pytest.mark.skipif(
    not (GATE_ENABLED and vis_native is not None),
    reason="Performance gate disabled (EF_BENCH_GATE!=1) or native modules unavailable",
)

_TRACE_PATH = "examples/vision_optical_flow/traces/inputs/vision.norm.jsonl"


def _get_trace_path() -> str:
    if not os.path.exists(_TRACE_PATH):
        pytest.skip(f"Missing input trace at {_TRACE_PATH} (skipping performance gates)")
    return _TRACE_PATH


_SINK = 0
def measure(fn: Callable[[], Any], reps: int = 3, warmup: int = 1, consume: Callable[[Any], int] | None = None) -> float:
    """
    Measure median wall time of fn() over reps after warmups.
    Ensures outputs are consumed to avoid dead-code elimination.
    """
    global _SINK
    for _ in range(warmup):
        out = fn()
        if consume is None:
            try:
                a, b = out  # type: ignore[misc]
                _SINK ^= int(getattr(a, "get", lambda k, d=None: None)("layout") is not None)
                _SINK ^= len(b) if hasattr(b, "__len__") else 0
            except Exception:
                _SINK ^= hash(str(out)) & 0xFFFFFFFF
        else:
            _SINK ^= int(consume(out)) & 0xFFFFFFFF
    times: list[float] = []
    for _ in range(reps):
        t0 = time.perf_counter()
        out = fn()
        t1 = time.perf_counter()
        if consume is None:
            try:
                a, b = out  # type: ignore[misc]
                _SINK ^= int(getattr(a, "get", lambda k, d=None: None)("layout") is not None)
                _SINK ^= len(b) if hasattr(b, "__len__") else 0
            except Exception:
                _SINK ^= hash(str(out)) & 0xFFFFFFFF
        else:
            _SINK ^= int(consume(out)) & 0xFFFFFFFF
        times.append(t1 - t0)
    return statistics.median(times)


def _get_thresh(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except Exception:
        return default


def python_coo_from_jsonl_ref(path: str, width: int, height: int, window_us: int, delay_us: int, edge_delay_us: int, min_count: int):
    """
    Minimal pass-through reference to mirror the example graph behavior used in tests.
    Returns (header: dict, events: list[dict]).
    """
    header = None
    events = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
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
                val = float(ev.get("val", 1.0))
                events.append({"ts": int(ts), "idx": [int(x), int(y), int(pol)], "val": val})
    events.sort(key=lambda e: (e["ts"], e["idx"][0], e["idx"][1], e["idx"][2]))
    if header is None:
        header = {"dims": ["x", "y", "polarity"], "layout": "coo"}
    return header, events


def _python_shift_delay_fuse_ref(path: str, width: int, height: int, window_us: int, delay_us: int, edge_delay_us: int, min_count: int):
    """
    Reference for shift(+/-1 x) + delay + coincidence fuse. Returns (header, events)
    """
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

    # Build shifted/delayed B streams
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

    # Fuse per coordinate with sliding windows
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
            if buf_a and buf_b and (len(buf_a) + len(buf_b)) >= int(min_count):
                x, y, pol = key
                out.append({"ts": t, "idx": [x, y, pol], "val": 1.0})
    out.sort(key=lambda e: (e["ts"], e["idx"][0], e["idx"][1], e["idx"][2]))
    if header is None:
        header = {"dims": ["x", "y", "polarity"], "layout": "coo"}
    return header, out


def _require_native_func(name: str):
    if vis_native is None or not hasattr(vis_native, name):
        pytest.skip(f"Native function {name} not available")


def test_gate_optical_flow_pass_speedup():
    _require_native_func("optical_flow_coo_from_jsonl")
    path = _get_trace_path()
    width = 128; height = 128
    window_us = 5000; delay_us = 2000; edge_delay_us = 200; min_count = 1

    def run_native():
        return vis_native.optical_flow_coo_from_jsonl(path, width, height, window_us, delay_us, edge_delay_us, min_count)  # type: ignore[attr-defined]

    def run_python():
        return python_coo_from_jsonl_ref(path, width, height, window_us, delay_us, edge_delay_us, min_count)

    t_n = measure(run_native, reps=3, warmup=1)
    t_p = measure(run_python, reps=3, warmup=1)
    speedup = t_p / t_n if t_n > 0 else float("inf")
    thresh = _get_thresh("MOD_PASS_MIN", 1.3)
    assert speedup >= thresh, f"optical_flow_coo_from_jsonl speedup {speedup:.2f}x < {thresh}x (native {t_n:.4f}s vs python {t_p:.4f}s)"


def test_gate_optical_flow_shift_delay_fuse_speedup():
    _require_native_func("optical_flow_shift_delay_fuse_coo")
    path = _get_trace_path()
    width = 128; height = 128
    window_us = 5000; delay_us = 2000; edge_delay_us = 200; min_count = 2

    def run_native():
        return vis_native.optical_flow_shift_delay_fuse_coo(path, width, height, window_us, delay_us, edge_delay_us, min_count)  # type: ignore[attr-defined]

    def run_python():
        return _python_shift_delay_fuse_ref(path, width, height, window_us, delay_us, edge_delay_us, min_count)

    t_n = measure(run_native, reps=3, warmup=1)
    t_p = measure(run_python, reps=3, warmup=1)
    speedup = t_p / t_n if t_n > 0 else float("inf")
    thresh = _get_thresh("MOD_FUSE_MIN", 1.5)
    assert speedup >= thresh, f"optical_flow_shift_delay_fuse_coo speedup {speedup:.2f}x < {thresh}x (native {t_n:.4f}s vs python {t_p:.4f}s)"