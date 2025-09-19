from __future__ import annotations
from typing import Any, Optional, Dict
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import STFT, MelBands

def stft_frontend(
    mic_source: Any,
    n_fft: int = 256,
    hop: str = "10 ms",
    sample_rate_hz: int = 16000,
    window: str = "hann",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Build a minimal STFT-only frontend graph.
    Input stream is expected to be PCM-like events: (t_ns, ch=0, value, {"unit":"pcm"}).
    """
    g = EIRGraph()
    g.add_node("stft", STFT("stft", n_fft=n_fft, hop=hop, sample_rate_hz=sample_rate_hz, window=window).as_op())
    return g

def mel_frontend(
    mic_source: Any,
    n_fft: int = 256,
    n_mels: int = 32,
    hop: str = "10 ms",
    sample_rate_hz: int = 16000,
    fmin_hz: float = 0.0,
    fmax_hz: Optional[float] = None,
    log: bool = True,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Build STFT -> Mel graph with deterministic software operators.
    """
    g = EIRGraph()
    g.add_node("stft", STFT("stft", n_fft=n_fft, hop=hop, sample_rate_hz=sample_rate_hz).as_op())
    g.add_node("mel", MelBands("mel", n_fft=n_fft, n_mels=n_mels, sample_rate_hz=sample_rate_hz, fmin_hz=fmin_hz, fmax_hz=fmax_hz, log=log).as_op())
    g.connect("stft", "spec", "mel", "in")
    return g
