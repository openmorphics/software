from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import DelayLine, EventFuse

def stress_index(
    bio_streams: Any,
    window: str = "60 s",
    params: Optional[Dict[str, Any]] = None
) -> EIRGraph:
    """
    Stress proxy: bursts of activity within a minute window.
    Provide events to node 'id' at runtime.
    """
    g = EIRGraph()
    g.add_node("id",    DelayLine("id", delay="0 ms").as_op())
    g.add_node("delay", DelayLine("delay", delay=window).as_op())
    g.add_node("stress", EventFuse("stress", window=window, min_count=3).as_op())
    g.connect("id", "out", "delay", "in")
    g.connect("id", "out", "stress", "a")
    g.connect("delay", "out", "stress", "b")
    return g
