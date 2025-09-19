from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import DelayLine
def hrv_index(heart_stream: Any, window: str = "1 s", params: Optional[Dict[str, Any]] = None) -> EIRGraph:
    g = EIRGraph()
    op = DelayLine("hrv", delay=window).as_op()
    g.add_node("hrv", op)
    return g
