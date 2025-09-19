from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import LIFNeuron, STFT, MelBands

def keyword_spotter(
    mic_source: Any,
    phrase: str = "hey eventflow",
    tau_m: str = "10 ms",
    v_th: float = 0.5,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Minimal KWS scaffold: STFT -> Mel -> LIF.
    """
    p = params or {}
    n_fft = int(p.get("n_fft", 128))
    hop = p.get("hop", "10 ms")
    sr = int(p.get("sample_rate_hz", 16000))
    n_mels = int(p.get("n_mels", 32))

    g = EIRGraph()
    g.add_node("stft", STFT("stft", n_fft=n_fft, hop=hop, sample_rate_hz=sr).as_op())
    g.add_node("mel", MelBands("mel", n_fft=n_fft, n_mels=n_mels, sample_rate_hz=sr).as_op())
    g.add_node("kws", LIFNeuron("kws", tau_m=tau_m, v_th=v_th).as_op())

    g.connect("stft", "spec", "mel", "in")
    g.connect("mel", "mel", "kws", "in")
    return g
