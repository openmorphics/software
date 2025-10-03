from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, XYToChannel, ShiftXY

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
