from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import LIFNeuron
def reflex_controller(sensor_stream: Any, tau_m: str = "5 ms", v_th: float = 0.5, params: Optional[Dict[str, Any]] = None) -> EIRGraph:
    g = EIRGraph()
    op = LIFNeuron("reflex", tau_m=tau_m, v_th=v_th).as_op()
    g.add_node("reflex", op)
    return g
