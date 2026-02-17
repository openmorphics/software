import wave
import numpy as np
from scipy import signal
from typing import Iterator
from ..api.source import BaseSource
from ..api.packet import EventPacket, audio_band_event
from ..sync.clock import ClockSync, ClockModel

class MicSource(BaseSource):
    def __init__(self, d: str = "default", b: int = 32, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._b, self._c = d, b, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "audio.mic", "device": self._d, "bands": self._b}
    def subscribe(self) -> Iterator[EventPacket]:
        # This is a stub for a live source, so it yields nothing.
        # A real implementation would connect to hardware.
        return
        yield

class WAVFileSource(BaseSource):
    def __init__(self, p: str, b: int = 32, hop: int = 10**7, **_):
        super().__init__()
        self._p, self._b, self._hop = p, b, hop
    def metadata(self): return {"kind": "audio.mic", "file": self._p, "bands": self._b}
    def subscribe(self) -> Iterator[EventPacket]:
        with wave.open(self._p, 'rb') as wf:
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            p_bytes = wf.readframes(n_frames)
            samples = np.frombuffer(p_bytes, dtype=np.int16)
            
            nperseg = 256  # STFT segment length
            f, t, Zxx = signal.stft(samples, fs=framerate, nperseg=nperseg)
            
            # For simplicity, we're not implementing mel-frequency scaling here,
            # but using the raw STFT bands. A full implementation would add a mel filterbank.
            # We'll map STFT frequency bins to the number of requested bands.
            
            for i, time_sec in enumerate(t):
                ts_ns = int(time_sec * 1e9)
                self._watermark_ns = ts_ns
                
                # Take the magnitude of the complex STFT output
                magnitudes = np.abs(Zxx[:, i])
                
                # Distribute the STFT magnitudes across the requested number of bands
                for band_idx in range(self._b):
                    # Simple mapping: average a slice of STFT bins for each band
                    start = int(band_idx * len(magnitudes) / self._b)
                    end = int((band_idx + 1) * len(magnitudes) / self._b)
                    if start < end:
                        band_magnitude = np.mean(magnitudes[start:end])
                    else:
                        band_magnitude = magnitudes[start] if start < len(magnitudes) else 0

                    event = audio_band_event(ts_ns, band_idx, m=band_magnitude)
                    yield event
