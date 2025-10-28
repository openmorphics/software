from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, STFT, MelBands, DelayLine

def voice_activity(
    mic_source: Any,
    window: str = "25 ms",
    min_bands: int = 3,
    params: Optional[Dict[str, Any]] = None,
    *,
    hangover: Optional[str] = None,
) -> EIRGraph:
    """
    Simple VAD pipeline:
      STFT -> Mel -> Fuse(coincidence across mel bands)
    Optional hangover extends post-detection presence by emitting a delayed copy.

    Ports and nodes:
      - Input expected at "stft" during runtime wiring
      - Nodes: "stft", "mel", "vad" (and optional "vad_hang" when hangover is provided)
    """
    p = params or {}
    n_fft = int(p.get("n_fft", 128))
    hop = p.get("hop", "10 ms")
    sr = int(p.get("sample_rate_hz", 16000))
    n_mels = int(p.get("n_mels", 32))

    g = EIRGraph()
    g.add_node("stft", STFT("stft", n_fft=n_fft, hop=hop, sample_rate_hz=sr).as_op())
    g.add_node("mel", MelBands("mel", n_fft=n_fft, n_mels=n_mels, sample_rate_hz=sr).as_op())
    g.add_node("vad", EventFuse("vad", window=window, min_count=min_bands).as_op())

    g.connect("stft", "spec", "mel", "in")
    # feed mel to both ports to detect multi-event coincidences in a window
    g.connect("mel", "mel", "vad", "a")
    g.connect("mel", "mel", "vad", "b")

    # Optional hangover: create a delayed copy of VAD output
    if hangover:
        g.add_node("vad_hang", DelayLine("vad_hang", delay=hangover).as_op())
        g.connect("vad", "out", "vad_hang", "in")

    return g
