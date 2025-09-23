from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import DelayLine, LIFNeuron

def music_generator(streams: Any, params: Optional[Dict[str, Any]] = None) -> EIRGraph:
    """
    A simple music generator scaffold that routes an input stream through
    a delay and a spiking neuron to create a basic generative system.
    Provide events to the 'in' node.
    """
    g = EIRGraph()
    p = params or {}
    delay_time = p.get("delay", "100 ms")
    tau_m = p.get("tau_m", "20 ms")
    v_th = p.get("v_th", 0.8)

    g.add_node("in", DelayLine("in", delay="0 ms").as_op())
    g.add_node("delay", DelayLine("delay", delay=delay_time).as_op())
    g.add_node("neuron", LIFNeuron("neuron", tau_m=tau_m, v_th=v_th).as_op())

    g.connect("in", "out", "delay", "in")
    g.connect("delay", "out", "neuron", "in")
    g.connect("neuron", "spike", "in", "in")  # Feedback loop

    return g
