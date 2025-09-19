from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine

def change_point(
    stream: Any,
    window: str = "200 ms",
    min_events: int = 2,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Change-point proxy: self-coincidence across a delay within a window.
    Provide events to node 'id' at runtime.
    """
    g = EIRGraph()
    g.add_node("id",    DelayLine("id", delay="0 ms").as_op())
    g.add_node("delay", DelayLine("delay", delay=window).as_op())
    g.add_node("cpd",   EventFuse("cpd", window=window, min_count=min_events).as_op())
    g.connect("id", "out", "delay", "in")
    g.connect("id", "out", "cpd", "a")
    g.connect("delay", "out", "cpd", "b")
    return g
