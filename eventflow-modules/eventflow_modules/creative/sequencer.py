from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine

def bio_sequencer(
    bio_stream: Any,
    tempo: str = "500 ms",
    params: Optional[Dict[str, Any]] = None
) -> EIRGraph:
    """
    Bio-adaptive sequencer: self-coincidence across a musical tempo delay.
    Provide events to node 'id' at runtime.
    """
    g = EIRGraph()
    g.add_node("id",    DelayLine("id", delay="0 ms").as_op())
    g.add_node("delay", DelayLine("delay", delay=tempo).as_op())
    g.add_node("sequencer", EventFuse("sequencer", window=tempo, min_count=1).as_op())
    g.connect("id", "out", "delay", "in")
    g.connect("id", "out", "sequencer", "a")
    g.connect("delay", "out", "sequencer", "b")
    return g
