from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, XYToChannel, ShiftXY
import json
import numpy as np
from ..errors import VisionError
from collections import deque, defaultdict

# Optional Rust acceleration for vision
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore

def optical_flow(
    source: Any,
    window: str = "2 ms",
    min_coincidences: int = 1,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Optical flow scaffold using event coincidences across spatial shifts:
    - xy: map DVS (x,y) to channel indices
    - shift_e: shift +x; delayed to align with current events
    - shift_w: shift -x; delayed similarly
    - flow_e/flow_w: coincidence detectors within a small window
    Provide events to node 'xy' input at runtime.
    """
    p = params or {}
    w = int(p.get("width", 128)); h = int(p.get("height", 128))
    delay = p.get("delay", "1 ms")

    g = EIRGraph()
    g.add_node("xy", XYToChannel("xy", width=w, height=h).as_op())

    # Eastward motion
    g.add_node("shift_e", ShiftXY("shift_e", dx=1, dy=0, width=w, height=h).as_op())
    g.add_node("delay_e", DelayLine("delay_e", delay=delay).as_op())
    g.add_node("flow_e", EventFuse("flow_e", window=window, min_count=min_coincidences).as_op())

    # Westward motion
    g.add_node("shift_w", ShiftXY("shift_w", dx=-1, dy=0, width=w, height=h).as_op())
    g.add_node("delay_w", DelayLine("delay_w", delay=delay).as_op())
    g.add_node("flow_w", EventFuse("flow_w", window=window, min_count=min_coincidences).as_op())

    # Wiring
    g.connect("xy", "ch", "shift_e", "in")
    g.connect("shift_e", "out", "delay_e", "in")
    g.connect("xy", "ch", "flow_e", "a")
    g.connect("delay_e", "out", "flow_e", "b")

    g.connect("xy", "ch", "shift_w", "in")
    g.connect("shift_w", "out", "delay_w", "in")
    g.connect("xy", "ch", "flow_w", "a")
    g.connect("delay_w", "out", "flow_w", "b")

    return g


def coincidence_flow_from_jsonl(
    path: str,
    width: int,
    height: int,
    window_us: int,
    delay_us: int,
    edge_delay_us: int,
    min_count: int,
    as_arrays: bool = False,
):
    """
    Return (header_dict, events) representing coincidence flow events computed
    from a normalized DVS JSONL input.

    - Default (as_arrays=False): events is a list of dicts
      {"ts": int, "idx": [x,y,pol], "val": 1.0}
    - Columnar mode (as_arrays=True): events is a dict of NumPy arrays with keys:
      {"ts": int64, "x": int64, "y": int64, "polarity": int64, "val": float32}

    Uses the native Rust implementation when available; otherwise falls back to
    a Python reference implementation. Existing callers are unaffected when
    as_arrays=False (default).
    """
    if as_arrays:
        # Prefer native columnar path if available
        if _ef_native_enabled() and _ef_native is not None and hasattr(_ef_native, "optical_flow_shift_delay_fuse_arrays"):
            return _ef_native.optical_flow_shift_delay_fuse_arrays(
                path, int(width), int(height), int(window_us), int(delay_us), int(edge_delay_us), int(min_count)
            )

        # Python fallback arrays with error normalization (raise VisionError on domain errors)
        if int(width) <= 0 or int(height) <= 0:
            raise VisionError("width/height must be > 0")
        if int(window_us) <= 0:
            raise VisionError("window_us must be > 0")
        if int(delay_us) < 0 or int(edge_delay_us) < 0:
            raise VisionError("delay_us and edge_delay_us must be >= 0")
        if int(min_count) <= 0:
            raise VisionError("min_count must be >= 1")

        # Compute via Python reference then convert to arrays
        hdr, events = coincidence_flow_from_jsonl(
            path, int(width), int(height), int(window_us), int(delay_us), int(edge_delay_us), int(min_count), as_arrays=False
        )
        n = len(events)
        if n == 0:
            zeros_i64 = np.empty((0,), dtype=np.int64)
            zeros_f32 = np.empty((0,), dtype=np.float32)
            arrays = {"ts": zeros_i64, "x": zeros_i64, "y": zeros_i64, "polarity": zeros_i64, "val": zeros_f32}
            return hdr, arrays

        ts = np.fromiter((e["ts"] for e in events), dtype=np.int64, count=n)
        x = np.fromiter((e["idx"][0] for e in events), dtype=np.int64, count=n)
        y = np.fromiter((e["idx"][1] for e in events), dtype=np.int64, count=n)
        pol = np.fromiter((e["idx"][2] for e in events), dtype=np.int64, count=n)
        val = np.full((n,), 1.0, dtype=np.float32)
        arrays = {"ts": ts, "x": x, "y": y, "polarity": pol, "val": val}
        return hdr, arrays

    """
    Return (header_dict, events_list) representing coincidence flow events computed
    from a normalized DVS JSONL input. Uses the native Rust implementation when
    available; otherwise falls back to a Python reference implementation.

    Each event in the output is a dict: {"ts": int, "idx": [x,y,pol], "val": 1.0}
    """
    # Use native if available
    if _ef_native_enabled() and _ef_native is not None and hasattr(_ef_native, "optical_flow_shift_delay_fuse_coo"):
        return _ef_native.optical_flow_shift_delay_fuse_coo(
            path, int(width), int(height), int(window_us), int(delay_us), int(edge_delay_us), int(min_count)
        )

    # Python fallback (mirrors tests' _python_shift_delay_fuse_ref)
    eff_delay = int(delay_us + edge_delay_us)
    header = None
    a_events = []
    with open(path, "r") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            ev = json.loads(s)
            if "header" in ev:
                header = ev["header"]
                continue
            ts = int(ev["ts"])
            x, y, pol = ev["idx"]
            if 0 <= x < width and 0 <= y < height and 0 <= pol <= 1:
                a_events.append({"ts": ts, "idx": [x, y, pol], "val": float(ev.get("val", 1.0))})
    a_events.sort(key=lambda e: e["ts"])

    # Build A and B (shifted+delayed) streams per coordinate
    a_map: dict[tuple[int, int, int], list[int]] = defaultdict(list)
    b_map: dict[tuple[int, int, int], list[int]] = defaultdict(list)
    for e in a_events:
        ts = e["ts"]; x, y, pol = e["idx"]
        a_map[(x, y, pol)].append(ts)
        b_ts = ts + eff_delay
        if x + 1 < width:
            b_map[(x + 1, y, pol)].append(b_ts)
        if x - 1 >= 0:
            b_map[(x - 1, y, pol)].append(b_ts)

    # Fuse per coordinate using a sliding window [t - window, t]
    out: list[dict] = []
    keys = set(a_map.keys()) | set(b_map.keys())
    for key in keys:
        va = sorted(a_map.get(key, []))
        vb = sorted(b_map.get(key, []))
        i = j = 0
        buf_a: deque[int] = deque()
        buf_b: deque[int] = deque()
        while i < len(va) or j < len(vb):
            take_a = j >= len(vb) or (i < len(va) and va[i] <= vb[j])
            if take_a:
                t = va[i]; i += 1; buf_a.append(t)
            else:
                t = vb[j]; j += 1; buf_b.append(t)
            cutoff = t - int(window_us)
            while buf_a and buf_a[0] < cutoff: buf_a.popleft()
            while buf_b and buf_b[0] < cutoff: buf_b.popleft()
            if buf_a and buf_b and (len(buf_a) + len(buf_b)) >= int(min_count):
                x, y, pol = key
                out.append({"ts": t, "idx": [x, y, pol], "val": 1.0})
    out.sort(key=lambda e: (e["ts"], e["idx"][0], e["idx"][1], e["idx"][2]))
    if header is None:
        header = {"schema_version": "0.1.0", "dims": ["x", "y", "polarity"], "units": {"time": "us", "value": "dimensionless"}, "dtype": "f32", "layout": "coo"}
    return header, out


def load_events_from_jsonl(path: str, width: int, height: int, as_arrays: bool = False):
    """
    Pass-through reader for normalized DVS JSONL.

    - When as_arrays=False (default), returns (header_dict, events_list) where each event is:
      {"ts": int, "idx": [x, y, pol], "val": 1.0}
    - When as_arrays=True, returns (header_dict, arrays_dict) with keys:
      {"ts": int64, "x": int64, "y": int64, "polarity": int64, "val": float32}

    Preserves dims from source header when present. Domain errors (width/height <= 0)
    raise VisionError. I/O errors propagate as IOError.
    """
    w = int(width); h = int(height)
    if w <= 0 or h <= 0:
        raise VisionError("width/height must be > 0")

    if as_arrays:
        # Prefer native columnar path
        if _ef_native_enabled() and _ef_native is not None and hasattr(_ef_native, "optical_flow_coo_arrays"):
            return _ef_native.optical_flow_coo_arrays(path, w, h)

        # Fallback: obtain list-of-dicts, then convert to arrays
        try:
            if _ef_native_enabled() and _ef_native is not None and hasattr(_ef_native, "optical_flow_coo_from_jsonl"):
                hdr, events = _ef_native.optical_flow_coo_from_jsonl(path, w, h, 0, 0, 0, 1)
            else:
                hdr = None
                events = []
                with open(path, "r") as f:
                    for line in f:
                        s = line.strip()
                        if not s:
                            continue
                        ev = json.loads(s)
                        if "header" in ev:
                            hdr = ev["header"]
                            continue
                        ts = int(ev["ts"])
                        x, y, pol = ev["idx"]
                        if 0 <= x < w and 0 <= y < h and 0 <= pol <= 1:
                            events.append({"ts": ts, "idx": [x, y, pol], "val": 1.0})
                events.sort(key=lambda e: (e["ts"], e["idx"][0], e["idx"][1], e["idx"][2]))
                if hdr is None:
                    hdr = {"schema_version": "0.1.0", "dims": ["x", "y", "polarity"], "units": {"time": "us", "value": "dimensionless"}, "dtype": "f32", "layout": "coo"}
        except OSError:
            # Keep I/O as IOError
            raise

        n = len(events)
        if n == 0:
            zeros_i64 = np.empty((0,), dtype=np.int64)
            zeros_f32 = np.empty((0,), dtype=np.float32)
            arrays = {"ts": zeros_i64, "x": zeros_i64, "y": zeros_i64, "polarity": zeros_i64, "val": zeros_f32}
            return hdr, arrays

        ts = np.fromiter((e["ts"] for e in events), dtype=np.int64, count=n)
        x = np.fromiter((e["idx"][0] for e in events), dtype=np.int64, count=n)
        y = np.fromiter((e["idx"][1] for e in events), dtype=np.int64, count=n)
        pol = np.fromiter((e["idx"][2] for e in events), dtype=np.int64, count=n)
        val = np.full((n,), 1.0, dtype=np.float32)
        arrays = {"ts": ts, "x": x, "y": y, "polarity": pol, "val": val}
        return hdr, arrays

    # List-of-dicts output
    if _ef_native_enabled() and _ef_native is not None and hasattr(_ef_native, "optical_flow_coo_from_jsonl"):
        return _ef_native.optical_flow_coo_from_jsonl(path, w, h, 0, 0, 0, 1)

    # Pure-Python fallback pass-through
    header = None
    events = []
    with open(path, "r") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            ev = json.loads(s)
            if "header" in ev:
                header = ev["header"]
                continue
            ts = int(ev["ts"])
            x, y, pol = ev["idx"]
            if 0 <= x < w and 0 <= y < h and 0 <= pol <= 1:
                events.append({"ts": ts, "idx": [x, y, pol], "val": 1.0})
    events.sort(key=lambda e: (e["ts"], e["idx"][0], e["idx"][1], e["idx"][2]))
    if header is None:
        header = {"schema_version": "0.1.0", "dims": ["x", "y", "polarity"], "units": {"time": "us", "value": "dimensionless"}, "dtype": "f32", "layout": "coo"}
    return header, events
