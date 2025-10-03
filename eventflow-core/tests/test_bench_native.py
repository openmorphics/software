from __future__ import annotations
import numpy as np
import pytest
from collections import deque

try:
    from eventflow_core._rust import native as core_native
except Exception:
    core_native = None  # type: ignore

def python_bucket_ref(t: np.ndarray, v: np.ndarray, dt_ns: int):
    t = np.asarray(t, dtype=np.int64)
    v = np.asarray(v, dtype=np.float32)
    dt = int(dt_ns)
    if dt <= 0:
        raise ValueError("dt_ns must be > 0")
    n = t.size
    if n == 0:
        return np.empty((0,), dtype=np.int64), np.empty((0,), dtype=np.float32)
    out_t = []
    out_v = []
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

def python_fuse_ref(t_a: np.ndarray, t_b: np.ndarray, window_ns: int, min_count: int):
    t_a = np.asarray(t_a, dtype=np.int64)
    t_b = np.asarray(t_b, dtype=np.int64)
    win = int(window_ns)
    minc = int(min_count)
    if win <= 0:
        raise ValueError("window_ns must be > 0")
    buf_a: deque[int] = deque()
    buf_b: deque[int] = deque()
    i = 0
    j = 0
    n_a = t_a.size
    n_b = t_b.size
    out_t = []
    out_v = []
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

@pytest.mark.parametrize("impl", ["native", "python"])
def test_bench_bucket_native_vs_python(benchmark, impl: str):
    # Data: N≈200k, monotonic timestamps with clustered repeats (zero steps)
    N = 200_000
    dt = 10
    rng = np.random.default_rng(20240929)
    steps = rng.integers(0, 5, size=N, dtype=np.int64)  # includes zeros for repeats
    t = np.cumsum(steps, dtype=np.int64)
    v = rng.standard_normal(size=N).astype(np.float32)

    if impl == "native":
        if core_native is None or not hasattr(core_native, "bucket_sum_i64_f32"):
            pytest.skip("Native bucket_sum_i64_f32 not available")
        def run():
            return core_native.bucket_sum_i64_f32(t, v, dt)
    else:
        def run():
            return python_bucket_ref(t, v, dt)

    t_out, v_out = benchmark(run)
    assert t_out.dtype == np.int64 and v_out.dtype == np.float32
    assert t_out.ndim == 1 and v_out.ndim == 1

@pytest.mark.parametrize("impl", ["native", "python"])
def test_bench_fuse_native_vs_python(benchmark, impl: str):
    # Two monotonic sequences with overlap
    Na = 120_000
    Nb = 110_000
    rng = np.random.default_rng(20240930)
    steps_a = rng.integers(1, 6, size=Na, dtype=np.int64)
    steps_b = rng.integers(1, 7, size=Nb, dtype=np.int64)
    t_a = np.cumsum(steps_a, dtype=np.int64)
    t_b = np.cumsum(steps_b, dtype=np.int64) + np.int64(50)  # slight offset for overlap
    window_ns = 1000
    min_count = 2

    if impl == "native":
        if core_native is None or not hasattr(core_native, "fuse_coincidence_i64"):
            pytest.skip("Native fuse_coincidence_i64 not available")
        def run():
            return core_native.fuse_coincidence_i64(t_a, t_b, int(window_ns), int(min_count))
    else:
        def run():
            return python_fuse_ref(t_a, t_b, int(window_ns), int(min_count))

    t_out, v_out = benchmark(run)
    assert t_out.dtype == np.int64 and v_out.dtype == np.float32
    assert t_out.ndim == 1 and v_out.ndim == 1