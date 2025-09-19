from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, XYToChannel, ShiftXY

def corner_tracking(
    source: Any,
    window: str = "5 ms",
    threshold: float = 1.0,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Corner proxy: coincidence between orthogonal spatial shifts.
    Provide events to node 'xy' input at runtime.
    """
    p = params or {}
    w = int(p.get("width", 128)); h = int(p.get("height", 128))

    g = EIRGraph()
    g.add_node("xy", XYToChannel("xy", width=w, height=h).as_op())
    g.add_node("shift_e", ShiftXY("shift_e", dx=1, dy=0, width=w, height=h).as_op())
    g.add_node("shift_n", ShiftXY("shift_n", dx=0, dy=-1, width=w, height=h).as_op())
    g.add_node("corners", EventFuse("corners", window=window, min_count=2).as_op())

    g.connect("xy", "ch", "shift_e", "in")
    g.connect("xy", "ch", "shift_n", "in")
    g.connect("shift_e", "out", "corners", "a")
    g.connect("shift_n", "out", "corners", "b")
    return g
