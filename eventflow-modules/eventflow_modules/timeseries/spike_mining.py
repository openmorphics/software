from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine

def spike_pattern_mining(
    stream: Any,
    params: Optional[Dict[str, Any]] = None
) -> EIRGraph:
    """
    Spike pattern mining proxy: self-coincidence across short delay.
    Provide events to node 'id' at runtime.
    """
    p = params or {}
    window = p.get("window", "50 ms")
    min_count = int(p.get("min_count", 2))

    g = EIRGraph()
    g.add_node("id",    DelayLine("id", delay="0 ms").as_op())
    g.add_node("delay", DelayLine("delay", delay=window).as_op())
    g.add_node("mine",  EventFuse("mine", window=window, min_count=min_count).as_op())
    g.connect("id", "out", "delay", "in")
    g.connect("id", "out", "mine", "a")
    g.connect("delay", "out", "mine", "b")
    return g
