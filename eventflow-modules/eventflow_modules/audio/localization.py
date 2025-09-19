from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, STFT, MelBands

def localization(
    mic_array_source: Any,
    window: str = "20 ms",
    min_events: int = 4,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    DOA scaffold: STFT -> Mel -> Fuse (multi-band co-activity proxy).
    """
    p = params or {}
    n_fft = int(p.get("n_fft", 128))
    hop = p.get("hop", "10 ms")
    sr = int(p.get("sample_rate_hz", 16000))
    n_mels = int(p.get("n_mels", 32))

    g = EIRGraph()
    g.add_node("stft", STFT("stft", n_fft=n_fft, hop=hop, sample_rate_hz=sr).as_op())
    g.add_node("mel", MelBands("mel", n_fft=n_fft, n_mels=n_mels, sample_rate_hz=sr).as_op())
    g.add_node("doa", EventFuse("doa", window=window, min_count=min_events).as_op())

    g.connect("stft", "spec", "mel", "in")
    g.connect("mel", "mel", "doa", "a")
    g.connect("mel", "mel", "doa", "b")
    return g
