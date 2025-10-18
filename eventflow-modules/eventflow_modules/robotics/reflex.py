from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import LIFNeuron

def reflex_controller(sensor_stream: Any, tau_m: str = "5 ms", v_th: float = 0.5, params: Optional[Dict[str, Any]] = None) -> EIRGraph:
    """
    Reflex controller proxy: a single LIF neuron.

    SAL binding:
      - Provide events to node 'reflex' at runtime.

    Validation:
      - tau_m must be a non-empty string
      - v_th must be > 0
    """
    if not isinstance(tau_m, str) or not tau_m.strip():
        raise ValueError("tau_m must be a non-empty string")
    if float(v_th) <= 0.0:
        raise ValueError("v_th must be > 0")

    g = EIRGraph()
    op = LIFNeuron("reflex", tau_m=tau_m, v_th=float(v_th)).as_op()
    g.add_node("reflex", op)
    return g
