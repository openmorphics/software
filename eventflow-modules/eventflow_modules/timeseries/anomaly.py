from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import LIFNeuron

def anomaly_detector(stream: Any, threshold: float = 2.0, tau_m: str = "50 ms", params: Optional[Dict[str, Any]] = None) -> EIRGraph:
    """
    Anomaly detector proxy: single LIF unit that spikes on integrated input above threshold.

    SAL binding:
      - Provide events to node 'anomaly' at runtime.

    Validation:
      - threshold must be > 0
      - tau_m must be a non-empty string
    """
    if float(threshold) <= 0.0:
        raise ValueError("threshold must be > 0")
    if not isinstance(tau_m, str) or not tau_m.strip():
        raise ValueError("tau_m must be a non-empty string")

    g = EIRGraph()
    op = LIFNeuron("anomaly", tau_m=tau_m, v_th=float(threshold)).as_op()
    g.add_node("anomaly", op)
    return g
