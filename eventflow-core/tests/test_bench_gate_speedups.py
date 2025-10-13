from __future__ import annotations
import os
import time
import statistics
from typing import Callable, Any
import numpy as np
import pytest

try:
    from eventflow_core._rust import native as core_native
except Exception:
    core_native = None  # type: ignore


def _env_on(name: str) -> bool:
    val = os.getenv(name)
    if val is None:
        return False
    v = val.strip().lower()
    return v in ("1", "true", "on", "yes", "enable")


GATE_ENABLED = os.getenv("EF_BENCH_GATE") == "1"

pytestmark = pytest.mark.skipif(
    not (GATE_ENABLED and core_native is not None),
    reason="Performance gate disabled (EF_BENCH_GATE!=1) or native core unavailable",
)

_SINK = 0
def measure(fn: Callable[[], Any], reps: int = 8, warmup: int = 2, consume: Callable[[Any], int] | None = None) -> float:
    """
    Measure median wall time of fn() over reps after warmups.
    Ensures outputs are consumed to avoid dead-code elimination.
    """
    global _SINK
    for _ in range(warmup):
        out = fn()
        if consume is None:
            # Default: expect tuple of arrays
            try:
                a, b = out  # type: ignore[misc]
                _SINK ^= int(getattr(a, "size", len(a))) ^ int(getattr(b, "size", len(b)))
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
                _SINK ^= int(getattr(a, "size", len(a))) ^ int(getattr(b, "size", len(b)))
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


def python_bucket_ref(t: np.ndarray, v: np.ndarray, dt_ns: int) -> tuple[np.ndarray, np.ndarray]:
    t = np.asarray(t, dtype=np.int64)
    v = np.asarray(v, dtype=np.float32)
    dt = int(dt_ns)
    if dt <= 0:
        raise ValueError("dt_ns must be > 0")
    n = t.size
    if n == 0:
        return np.empty((0,), dtype=np.int64), np.empty((0,), dtype=np.float32)
    out_t: list[int] = []
    out_v: list[float] = []
    prev_key = (int(t[0]) // dt) * dt
    acc = float(v[0])
    for i in range(1, n):
        key = (int(t[i]) // dt) * dt
        if key == prev_key:
            acc += float(v[i])
        else:
            out_t.append(prev_key + dt)
            out_v.append(acc)
            prev_key = key
            acc = float(v[i])
    out_t.append(prev_key + dt)
    out_v.append(acc)
    return np.asarray(out_t, dtype=np.int64), np.asarray(out_v, dtype=np.float32)


def python_fuse_ref(t_a: np.ndarray, t_b: np.ndarray, window_ns: int, min_count: int) -> tuple[np.ndarray, np.ndarray]:
    from collections import deque
    t_a = np.asarray(t_a, dtype=np.int64)
    t_b = np.asarray(t_b, dtype=np.int64)
    win = int(window_ns)
    minc = int(min_count)
    if win <= 0:
        raise ValueError("window_ns must be > 0")
    buf_a: deque[int] = deque()
    buf_b: deque[int] = deque()
    i = j = 0
    n_a = t_a.size
    n_b = t_b.size
    out_t: list[int] = []
    out_v: list[float] = []
    while i < n_a or j < n_b:
        take_a = j >= n_b or (i < n_a and int(t_a[i]) <= int(t_b[j]))
        if take_a:
            t = int(t_a[i]); buf_a.append(t); i += 1
        else:
            t = int(t_b[j]); buf_b.append(t); j += 1
        cutoff = t - win
        while buf_a and buf_a[0] < cutoff:
            buf_a.popleft()
        while buf_b and buf_b[0] < cutoff:
            buf_b.popleft()
        total = len(buf_a) + len(buf_b)
        if total >= minc and buf_a and buf_b:
            out_t.append(t)
            out_v.append(1.0)
    return np.asarray(out_t, dtype=np.int64), np.asarray(out_v, dtype=np.float32)


def _require_native_func(name: str):
    if core_native is None or not hasattr(core_native, name):
        pytest.skip(f"Native function {name} not available")


def test_gate_bucket_sum_speedup():
    _require_native_func("bucket_sum_i64_f32")
    # Data: N≈50k, clustered repeats
    N = 50_000
    dt = 10
    rng = np.random.default_rng(20241003)
    steps = rng.integers(0, 5, size=N, dtype=np.int64)
    t = np.cumsum(steps, dtype=np.int64)
    v = rng.standard_normal(size=N).astype(np.float32)

    def run_native():
        return core_native.bucket_sum_i64_f32(t, v, int(dt))  # type: ignore[attr-defined]

    def run_python():
        return python_bucket_ref(t, v, int(dt))

    # Keep runtime short but stable
    t_n = measure(run_native, reps=6, warmup=2)
    t_p = measure(run_python, reps=4, warmup=2)
    speedup = t_p / t_n if t_n > 0 else float("inf")
    thresh = _get_thresh("CORE_BUCKET_MIN", 1.5)
    assert speedup >= thresh, f"bucket_sum_i64_f32 speedup {speedup:.2f}x < {thresh}x (native {t_n:.4f}s vs python {t_p:.4f}s)"


def test_gate_fuse_coincidence_speedup():
    _require_native_func("fuse_coincidence_i64")
    Na = 50_000
    Nb = 50_000
    rng = np.random.default_rng(20241004)
    steps_a = rng.integers(1, 6, size=Na, dtype=np.int64)
    steps_b = rng.integers(1, 7, size=Nb, dtype=np.int64)
    t_a = np.cumsum(steps_a, dtype=np.int64)
    t_b = np.cumsum(steps_b, dtype=np.int64) + np.int64(50)
    window_ns = 1000
    min_count = 2

    def run_native():
        return core_native.fuse_coincidence_i64(t_a, t_b, int(window_ns), int(min_count))  # type: ignore[attr-defined]

    def run_python():
        return python_fuse_ref(t_a, t_b, int(window_ns), int(min_count))

    t_n = measure(run_native, reps=5, warmup=2)
    t_p = measure(run_python, reps=4, warmup=2)
    speedup = t_p / t_n if t_n > 0 else float("inf")
    thresh = _get_thresh("CORE_FUSE_MIN", 1.5)
    assert speedup >= thresh, f"fuse_coincidence_i64 speedup {speedup:.2f}x < {thresh}x (native {t_n:.4f}s vs python {t_p:.4f}s)"