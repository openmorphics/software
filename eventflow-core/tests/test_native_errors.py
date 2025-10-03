from __future__ import annotations
import numpy as np
import pytest

try:
    from eventflow_core._rust import native as core_native  # type: ignore
except Exception:
    core_native = None  # type: ignore[assignment]

try:
    import eventflow_core.errors as ef_errors  # type: ignore
except Exception:
    ef_errors = None  # type: ignore[assignment]


def require_native():
    if core_native is None:
        pytest.skip("eventflow_core native not available", allow_module_level=False)


def require_core_func(name: str):
    require_native()
    if not hasattr(core_native, name):
        pytest.skip(f"eventflow_core native function '{name}' not available", allow_module_level=False)


@pytest.mark.skipif(core_native is None, reason="native core not available")
def test_bucket_sum_errors_dt_nonpositive():
    require_core_func("bucket_sum_i64_f32")
    t = np.array([0, 1], dtype=np.int64)
    v = np.array([1.0, 2.0], dtype=np.float32)
    with pytest.raises(ef_errors.BucketError):  # type: ignore[attr-defined]
        core_native.bucket_sum_i64_f32(t, v, 0)
    with pytest.raises(ef_errors.BucketError):  # type: ignore[attr-defined]
        core_native.bucket_sum_i64_f32(t, v, -5)


@pytest.mark.skipif(core_native is None, reason="native core not available")
def test_bucket_sum_errors_length_mismatch():
    require_core_func("bucket_sum_i64_f32")
    t = np.array([0, 1, 2], dtype=np.int64)
    v = np.array([1.0, 2.0], dtype=np.float32)
    with pytest.raises(ef_errors.BucketError):  # type: ignore[attr-defined]
        core_native.bucket_sum_i64_f32(t, v, 10)


@pytest.mark.skipif(core_native is None, reason="native core not available")
def test_fuse_coincidence_error_window_nonpositive():
    require_core_func("fuse_coincidence_i64")
    ta = np.array([], dtype=np.int64)
    tb = np.array([], dtype=np.int64)
    with pytest.raises(ef_errors.FuseError):  # type: ignore[attr-defined]
        core_native.fuse_coincidence_i64(ta, tb, 0, 1)
    with pytest.raises(ef_errors.FuseError):  # type: ignore[attr-defined]
        core_native.fuse_coincidence_i64(ta, tb, -1, 1)


@pytest.mark.skipif(core_native is None, reason="native core not available")
def test_logging_bridge_basic():
    require_native()
    if not hasattr(core_native, "set_log_sink"):
        pytest.skip("set_log_sink not available on native module", allow_module_level=False)
    captured: list[tuple[str, str]] = []

    def sink(level, message):
        captured.append((level, message))

    core_native.set_log_sink(sink)
    try:
        if hasattr(core_native, "log_emit"):
            core_native.log_emit("INFO", "hello")
            assert captured == [("INFO", "hello")]
        else:
            pytest.skip("log_emit not available on native module", allow_module_level=False)
    finally:
        # Clear sink
        core_native.set_log_sink(None)