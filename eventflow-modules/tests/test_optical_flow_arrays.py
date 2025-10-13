from __future__ import annotations
import os
import numpy as np
import pytest

from eventflow_modules.vision.optical_flow import coincidence_flow_from_jsonl
from eventflow_modules.errors import VisionError

def _trace_path():
    path = "examples/vision_optical_flow/traces/inputs/vision.norm.jsonl"
    if not os.path.exists(path):
        pytest.skip(f"Test trace not found at {os.path.abspath(path)}")
    return path

def test_arrays_dtype_and_shape():
    path = _trace_path()
    width = 128; height = 128
    window_us = 5000; delay_us = 2000; edge_delay_us = 200; min_count = 2

    hdr, cols = coincidence_flow_from_jsonl(path, width, height, window_us, delay_us, edge_delay_us, min_count, as_arrays=True)
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

def test_arrays_equivalence_with_coo():
    path = _trace_path()
    width = 128; height = 128
    window_us = 5000; delay_us = 2000; edge_delay_us = 200; min_count = 2

    hdr1, cols = coincidence_flow_from_jsonl(path, width, height, window_us, delay_us, edge_delay_us, min_count, as_arrays=True)
    hdr2, events = coincidence_flow_from_jsonl(path, width, height, window_us, delay_us, edge_delay_us, min_count, as_arrays=False)

    assert isinstance(events, list)
    cols2 = _events_to_arrays(events)

    # Sort both by (ts, x, y, polarity)
    def _order(c):
        return np.lexsort((c["polarity"], c["y"], c["x"], c["ts"]))
    ord1 = _order(cols)
    ord2 = _order(cols2)

    for k in ("ts","x","y","polarity","val"):
        assert np.array_equal(cols[k][ord1], cols2[k][ord2])

def test_arrays_error_mapping():
    path = _trace_path()
    width = 128; height = 128
    window_us = 5000; delay_us = 2000; edge_delay_us = 200; min_count = 2

    with pytest.raises(VisionError):
        coincidence_flow_from_jsonl(path, 0, height, window_us, delay_us, edge_delay_us, min_count, as_arrays=True)
    with pytest.raises(VisionError):
        coincidence_flow_from_jsonl(path, width, height, 0, delay_us, edge_delay_us, min_count, as_arrays=True)