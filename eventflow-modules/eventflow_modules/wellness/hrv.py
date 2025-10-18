from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import DelayLine, EventFuse

def hrv_index(heart_stream: Any, window: str = "1 s", params: Optional[Dict[str, Any]] = None) -> EIRGraph:
    """
    HRV proxy v1: self-coincidence within an epoch window as a proxy for variability.

    SAL binding:
      - Provide events to node 'id' at runtime.

    Notes:
      - Placeholder implementation using Delay+Fuse; an RR-interval-based metric is planned.
    """
    if not isinstance(window, str) or not window.strip():
        raise ValueError("window must be a non-empty string")

    g = EIRGraph()
    g.add_node("id", DelayLine("id", delay="0 ms").as_op())
    g.add_node("delay", DelayLine("delay", delay=window).as_op())
    g.add_node("hrv", EventFuse("hrv", window=window, min_count=2).as_op())
    g.connect("id", "out", "delay", "in")
    g.connect("id", "out", "hrv", "a")
    g.connect("delay", "out", "hrv", "b")
    return g
