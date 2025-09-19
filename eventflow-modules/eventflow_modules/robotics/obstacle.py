from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse

def obstacle_avoidance(
    depth_or_flow: Any,
    window: str = "15 ms",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Obstacle proxy: treat dense coincident events as obstacles.
    """
    g = EIRGraph()
    op = EventFuse("obstacle", window=window, min_count=3).as_op()
    g.add_node("obstacle", op)
    return g
