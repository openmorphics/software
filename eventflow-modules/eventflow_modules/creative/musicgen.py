from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import DelayLine, LIFNeuron

def music_generator(streams: Any, params: Optional[Dict[str, Any]] = None) -> EIRGraph:
    """
    Music generator proxy.

    Topology:
      in -> delay -> neuron --(spike)--> in (feedback loop)

    SAL binding:
      - Provide events to node 'in' at runtime.

    Validation:
      - tau_m must be a non-empty string
      - v_th must be > 0

    Notes:
      - This scaffold includes a feedback loop. Choose parameters (tau_m, v_th, refractory)
        to avoid runaway oscillations for your workload.
    """
    g = EIRGraph()
    p = params or {}
    delay_time = p.get("delay", "100 ms")
    tau_m = p.get("tau_m", "20 ms")
    v_th = p.get("v_th", 0.8)
    refractory = p.get("refractory", "2 ms")

    if not isinstance(tau_m, str) or not tau_m.strip():
        raise ValueError("tau_m must be a non-empty string")
    if float(v_th) <= 0.0:
        raise ValueError("v_th must be > 0")

    g.add_node("in", DelayLine("in", delay="0 ms").as_op())
    g.add_node("delay", DelayLine("delay", delay=delay_time).as_op())
    g.add_node("neuron", LIFNeuron("neuron", tau_m=tau_m, v_th=float(v_th), refractory=refractory).as_op())

    g.connect("in", "out", "delay", "in")
    g.connect("delay", "out", "neuron", "in")
    g.connect("neuron", "spike", "in", "in")  # Feedback loop

    return g
