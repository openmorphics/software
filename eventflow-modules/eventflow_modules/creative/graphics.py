from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import DelayLine

def event_graphics(streams: Any, params: Optional[Dict[str, Any]] = None) -> EIRGraph:
    """
    Pass-through visualizer scaffold: provides an identity delay node.
    Provide events to node 'gfx' at runtime.
    """
    g = EIRGraph()
    g.add_node("gfx", DelayLine("gfx", delay="0 ms").as_op())
    return g
