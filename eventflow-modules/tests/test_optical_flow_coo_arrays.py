from __future__ import annotations
import os
import numpy as np
import pytest

from eventflow_modules.vision.optical_flow import load_events_from_jsonl
from eventflow_modules.errors import VisionError


def _trace_path():
    path = "examples/vision_optical_flow/traces/inputs/vision.norm.jsonl"
    if not os.path.exists(path):
        pytest.skip(f"Test trace not found at {os.path.abspath(path)}")
    return path


def test_dtype_and_shape_arrays():
    path = _trace_path()
    hdr, cols = load_events_from_jsonl(path, 128, 128, as_arrays=True)
    assert isinstance(hdr, dict)
    assert isinstance(cols, dict)
    assert set(cols.keys()) == {"ts", "x", "y", "polarity", "val"}
    n = len(cols["ts"])
    assert cols["ts"].dtype == np.int64
    assert cols["x"].dtype == np.int64
    assert cols["y"].dtype == np.int64
    assert cols["polarity"].dtype == np.int64
    assert cols["val"].dtype == np.float32
    assert cols["x"].shape == cols["y"].shape == cols["polarity"].shape == cols["val"].shape == cols["ts"].shape
    if n > 0:
        assert cols["val"].shape == (n,)


def _events_to_arrays(events):
    n = len(events)
    ts = np.fromiter((e["ts"] for e in events), dtype=np.int64, count=n)
    x = np.fromiter((e["idx"][0] for e in events), dtype=np.int64, count=n)
    y = np.fromiter((e["idx"][1] for e in events), dtype=np.int64, count=n)
    pol = np.fromiter((e["idx"][2] for e in events), dtype=np.int64, count=n)
    val = np.full((n,), 1.0, dtype=np.float32)
    return {"ts": ts, "x": x, "y": y, "polarity": pol, "val": val}


def test_equivalence_with_list_of_dicts_sorted():
    path = _trace_path()
    hdr1, cols = load_events_from_jsonl(path, 128, 128, as_arrays=True)
    hdr2, events = load_events_from_jsonl(path, 128, 128, as_arrays=False)
    assert isinstance(events, list)
    cols2 = _events_to_arrays(events)
    def _order(c):
        return np.lexsort((c["polarity"], c["y"], c["x"], c["ts"]))
    ord1 = _order(cols)
    ord2 = _order(cols2)
    for k in ("ts", "x", "y", "polarity", "val"):
        assert np.array_equal(cols[k][ord1], cols2[k][ord2])


@pytest.mark.parametrize("impl", ["native", "python"])
def test_error_mapping_width_height_zero_visionerror(monkeypatch, impl):
    path = _trace_path()
    if impl == "native":
        monkeypatch.setenv("EF_NATIVE", "1")
    else:
        monkeypatch.setenv("EF_NATIVE", "0")
    with pytest.raises(VisionError):
        load_events_from_jsonl(path, 0, 128, as_arrays=True)
    with pytest.raises(VisionError):
        load_events_from_jsonl(path, 128, 0, as_arrays=True)