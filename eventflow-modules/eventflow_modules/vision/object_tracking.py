from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, XYToChannel

def object_tracking(
    source: Any,
    window: str = "20 ms",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Tracking proxy: persistence via self-coincidence across a short delay.
    Provide events to node 'xy' input at runtime.
    """
    p = params or {}
    w = int(p.get("width", 128)); h = int(p.get("height", 128))
    delay = p.get("delay", "5 ms")

    g = EIRGraph()
    g.add_node("xy", XYToChannel("xy", width=w, height=h).as_op())
    g.add_node("delay", DelayLine("delay", delay=delay).as_op())
    g.add_node("track", EventFuse("track", window=window, min_count=2).as_op())
    g.connect("xy", "ch", "delay", "in")
    g.connect("xy", "ch", "track", "a")
    g.connect("delay", "out", "track", "b")
    return g
