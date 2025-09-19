from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import DelayLine, EventFuse

def sleep_staging(
    bio_streams: Any,
    window: str = "30 s",
    params: Optional[Dict[str, Any]] = None
) -> EIRGraph:
    """
    Sleep staging proxy: periodicity/coincidence over epoch window.
    Provide events to node 'id' at runtime.
    """
    g = EIRGraph()
    g.add_node("id",    DelayLine("id", delay="0 ms").as_op())
    g.add_node("delay", DelayLine("delay", delay=window).as_op())
    g.add_node("sleep", EventFuse("sleep", window=window, min_count=2).as_op())
    g.connect("id", "out", "delay", "in")
    g.connect("id", "out", "sleep", "a")
    g.connect("delay", "out", "sleep", "b")
    return g
