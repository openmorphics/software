from __future__ import annotations
import os
import pytest

# Loader and error alias
try:
    from eventflow_modules._rust import native as vis_native  # type: ignore
except Exception:
    vis_native = None  # type: ignore[assignment]

from eventflow_modules import errors as mod_errors  # type: ignore


def _get_trace_path():
    path = "examples/vision_optical_flow/traces/inputs/vision.norm.jsonl"
    if not os.path.exists(path):
        pytest.skip(f"Test trace not found at {os.path.abspath(path)}")
    return path


def _require_native():
    if vis_native is None:
        pytest.skip("Native vision module not available")
    # Ensure kernels are present
    if not hasattr(vis_native, "optical_flow_coo_from_jsonl"):
        pytest.skip("optical_flow_coo_from_jsonl not present in native module")
    if not hasattr(vis_native, "optical_flow_shift_delay_fuse_coo"):
        pytest.skip("optical_flow_shift_delay_fuse_coo not present in native module")


def test_error_mapping_invalid_dims():
    _require_native()
    path = _get_trace_path()
    with pytest.raises(mod_errors.VisionError):
        # width = 0 should raise a domain error mapped to VisionError
        vis_native.optical_flow_coo_from_jsonl(path, 0, 128, 5000, 2000, 200, 1)


@pytest.mark.parametrize(
    "kwargs",
    [
        dict(window_us=0, delay_us=2000, edge_delay_us=200, min_count=2),
        dict(window_us=5000, delay_us=2000, edge_delay_us=200, min_count=0),
    ],
)
def test_error_mapping_invalid_params(kwargs):
    _require_native()
    path = _get_trace_path()
    with pytest.raises(mod_errors.VisionError):
        vis_native.optical_flow_shift_delay_fuse_coo(
            path,
            128,
            128,
            kwargs["window_us"],
            kwargs["delay_us"],
            kwargs["edge_delay_us"],
            kwargs["min_count"],
        )


def test_logging_bridge_roundtrip():
    _require_native()
    seen: list[tuple[str, str]] = []

    def sink(level: str, msg: str):
        seen.append((level, msg))

    # set sink via native bridge
    assert hasattr(vis_native, "set_log_sink"), "native module must export set_log_sink"
    vis_native.set_log_sink(sink)
    try:
        assert hasattr(vis_native, "log_emit"), "native module must export log_emit"
        vis_native.log_emit("INFO", "hello-modules")
        assert ("INFO", "hello-modules") in seen
    finally:
        # Clear sink
        vis_native.set_log_sink(None)