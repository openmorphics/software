from __future__ import annotations
import numpy as np
import pytest
from collections import deque

try:
    from eventflow_core._rust import native as core_native
except Exception:
    core_native = None  # type: ignore

def require_core_func(name: str):
    if core_native is None or not hasattr(core_native, name):
        pytest.skip(f"eventflow_core native function '{name}' not available", allow_module_level=False)

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

@pytest.mark.parametrize("dt", [1, 10, 100])
def test_bucket_sum_parity_empty_and_single(dt):
    require_core_func("bucket_sum_i64_f32")
    t_empty = np.array([], dtype=np.int64)
    v_empty = np.array([], dtype=np.float32)
    t_out_n, v_out_n = core_native.bucket_sum_i64_f32(t_empty, v_empty, int(dt))
    t_out_p, v_out_p = python_bucket_ref(t_empty, v_empty, int(dt))
    np.testing.assert_array_equal(t_out_n, t_out_p)
    np.testing.assert_allclose(v_out_n, v_out_p, rtol=1e-7, atol=0)

    t_one = np.array([0], dtype=np.int64)
    v_one = np.array([3.5], dtype=np.float32)
    t_out_n, v_out_n = core_native.bucket_sum_i64_f32(t_one, v_one, int(dt))
    t_out_p, v_out_p = python_bucket_ref(t_one, v_one, int(dt))
    np.testing.assert_array_equal(t_out_n, t_out_p)
    np.testing.assert_allclose(v_out_n, v_out_p, rtol=1e-7, atol=0)

def test_bucket_sum_parity_grouping_and_boundaries():
    require_core_func("bucket_sum_i64_f32")
    dt = 10
    # Times straddle boundaries; include exact boundary timestamps
    t = np.array([0, 1, 2, 9, 10, 10, 19, 20, 29, 30, 30, 31], dtype=np.int64)
    v = np.array([1, 2, 3, 4,  5,  6,  7,  8,  9, 10, 11, 12], dtype=np.float32)
    # Ensure sorted ascending
    order = np.argsort(t, kind="stable")
    t = t[order]; v = v[order]
    t_out_n, v_out_n = core_native.bucket_sum_i64_f32(t, v, dt)
    t_out_p, v_out_p = python_bucket_ref(t, v, dt)
    np.testing.assert_array_equal(t_out_n, t_out_p)
    np.testing.assert_allclose(v_out_n, v_out_p, rtol=1e-7, atol=0)

@pytest.mark.parametrize("dt", [1, 10, 100])
def test_bucket_sum_parity_randomized(dt):
    require_core_func("bucket_sum_i64_f32")
    rng = np.random.default_rng(12345 + dt)
    N = 5000
    # Generate random timestamps with some clustering and boundaries
    base = rng.integers(0, 100000, size=N, dtype=np.int64)
    # Inject some exact bucket boundaries
    if N >= 10:
        base[:10] = (base[:10] // dt) * dt
    t = np.sort(base, kind="stable")
    v = rng.standard_normal(size=N).astype(np.float32)
    t_out_n, v_out_n = core_native.bucket_sum_i64_f32(t, v, int(dt))
    t_out_p, v_out_p = python_bucket_ref(t, v, int(dt))
    np.testing.assert_array_equal(t_out_n, t_out_p)
    np.testing.assert_allclose(v_out_n, v_out_p, rtol=1e-7, atol=0)

def test_fuse_coincidence_parity_no_events():
    require_core_func("fuse_coincidence_i64")
    t_a = np.array([], dtype=np.int64)
    t_b = np.array([], dtype=np.int64)
    window = 100
    minc = 1
    t_out_n, v_out_n = core_native.fuse_coincidence_i64(t_a, t_b, int(window), int(minc))
    t_out_p, v_out_p = python_fuse_ref(t_a, t_b, int(window), int(minc))
    np.testing.assert_array_equal(t_out_n, t_out_p)
    np.testing.assert_allclose(v_out_n, v_out_p, rtol=1e-7, atol=0)

@pytest.mark.parametrize("only_stream", ["a", "b"])
def test_fuse_coincidence_parity_single_stream_only(only_stream):
    require_core_func("fuse_coincidence_i64")
    t_a = np.array([0, 50, 100, 150], dtype=np.int64) if only_stream == "a" else np.array([], dtype=np.int64)
    t_b = np.array([25, 75, 125], dtype=np.int64) if only_stream == "b" else np.array([], dtype=np.int64)
    window = 40
    minc = 2
    t_out_n, v_out_n = core_native.fuse_coincidence_i64(t_a, t_b, int(window), int(minc))
    t_out_p, v_out_p = python_fuse_ref(t_a, t_b, int(window), int(minc))
    np.testing.assert_array_equal(t_out_n, t_out_p)
    np.testing.assert_allclose(v_out_n, v_out_p, rtol=1e-7, atol=0)

def test_fuse_coincidence_parity_interleaved():
    require_core_func("fuse_coincidence_i64")
    t_a = np.array([0, 100, 250, 400, 650, 900], dtype=np.int64)
    t_b = np.array([50, 300, 450, 700, 950], dtype=np.int64)
    window = 120
    minc = 2
    t_out_n, v_out_n = core_native.fuse_coincidence_i64(t_a, t_b, int(window), int(minc))
    t_out_p, v_out_p = python_fuse_ref(t_a, t_b, int(window), int(minc))
    np.testing.assert_array_equal(t_out_n, t_out_p)
    np.testing.assert_allclose(v_out_n, v_out_p, rtol=1e-7, atol=0)

def test_fuse_coincidence_parity_identical_timestamps_batches():
    require_core_func("fuse_coincidence_i64")
    t = 1000
    t_a = np.array([t]*5, dtype=np.int64)
    t_b = np.array([t]*7, dtype=np.int64)
    window = 10
    for minc in (1, 2, 3, 10):
        t_out_n, v_out_n = core_native.fuse_coincidence_i64(t_a, t_b, int(window), int(minc))
        t_out_p, v_out_p = python_fuse_ref(t_a, t_b, int(window), int(minc))
        np.testing.assert_array_equal(t_out_n, t_out_p)
        np.testing.assert_allclose(v_out_n, v_out_p, rtol=1e-7, atol=0)

@pytest.mark.parametrize("window,minc", [(5, 2), (50, 2), (200, 3), (1000, 4)])
def test_fuse_coincidence_parity_randomized(window, minc):
    require_core_func("fuse_coincidence_i64")
    rng = np.random.default_rng(20240929 + window + minc)
    Na = 2000
    Nb = 2200
    steps_a = rng.integers(1, 7, size=Na, dtype=np.int64)
    steps_b = rng.integers(1, 9, size=Nb, dtype=np.int64)
    t_a = np.cumsum(steps_a)
    t_b = np.cumsum(steps_b) + rng.integers(0, 50, dtype=np.int64)
    # Ensure monotonicity and realistic overlap
    t_a = np.asarray(t_a, dtype=np.int64)
    t_b = np.asarray(t_b, dtype=np.int64)
    t_out_n, v_out_n = core_native.fuse_coincidence_i64(t_a, t_b, int(window), int(minc))
    t_out_p, v_out_p = python_fuse_ref(t_a, t_b, int(window), int(minc))
    np.testing.assert_array_equal(t_out_n, t_out_p)
    np.testing.assert_allclose(v_out_n, v_out_p, rtol=1e-7, atol=0)