from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse
def gesture_detect(flow_graph_or_source: Any, window: str = "50 ms", min_events: int = 20, params: Optional[Dict[str, Any]] = None) -> EIRGraph:
    g = EIRGraph()
    op = EventFuse("gesture", window=window, min_count=min_events).as_op()
    g.add_node("gesture", op)
    return g
