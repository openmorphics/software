from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import LIFNeuron
def anomaly_detector(stream: Any, threshold: float = 2.0, tau_m: str = "50 ms", params: Optional[Dict[str, Any]] = None) -> EIRGraph:
    g = EIRGraph()
    op = LIFNeuron("anomaly", tau_m=tau_m, v_th=threshold).as_op()
    g.add_node("anomaly", op)
    return g
