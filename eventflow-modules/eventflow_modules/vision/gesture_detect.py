from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine
from ..errors import VisionError

def gesture_detect(flow_graph_or_source: Any, window: str = "50 ms", min_events: int = 20, params: Optional[Dict[str, Any]] = None) -> EIRGraph:
    """
    Gesture detection proxy.

    SAL binding:
      - Provide events to node 'id' at runtime. This stub detects bursts of activity
        via self-coincidence within a time window.

    Validation:
      - window must be a non-empty string, min_events >= 1
      - Raises VisionError on invalid parameters to align with native error semantics.
    """
    if not isinstance(window, str) or not window.strip():
        raise VisionError("window must be a non-empty string")
    if int(min_events) < 1:
        raise VisionError("min_events must be >= 1")

    g = EIRGraph()
    g.add_node("id", DelayLine("id", delay="0 ms").as_op())
    g.add_node("gesture", EventFuse("gesture", window=window, min_count=int(min_events)).as_op())
    g.connect("id", "out", "gesture", "a")
    g.connect("id", "out", "gesture", "b")
    return g
