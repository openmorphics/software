from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine

def obstacle_avoidance(
    depth_or_flow: Any,
    window: str = "15 ms",
    min_count: int = 3,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Obstacle proxy: treat dense coincident events as obstacles.

    SAL binding:
      - Provide events to node 'id' at runtime.

    Validation:
      - window must be a non-empty string
      - min_count must be >= 1
    """
    if not isinstance(window, str) or not window.strip():
        raise ValueError("window must be a non-empty string")
    if int(min_count) < 1:
        raise ValueError("min_count must be >= 1")

    g = EIRGraph()
    g.add_node("id", DelayLine("id", delay="0 ms").as_op())
    op = EventFuse("obstacle", window=window, min_count=int(min_count)).as_op()
    g.add_node("obstacle", op)
    g.connect("id", "out", "obstacle", "a")
    g.connect("id", "out", "obstacle", "b")
    return g
