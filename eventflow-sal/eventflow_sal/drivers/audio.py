from typing import Iterator
from ..api.source import BaseSource
from ..api.packet import EventPacket, audio_band_event
from ..sync.clock import ClockSync, ClockModel

class MicSource(BaseSource):
    def __init__(self, d: str = "default", b: int = 32, c: "ClockSync|None" = None, **_):
        self._d, self._b, self._c = d, b, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "audio.mic", "device": self._d, "bands": self._b}
    def subscribe(self) -> Iterator[EventPacket]:
        raise ValueError("sal.unsupported_source: live microphone capture not implemented")

class WAVFileSource(BaseSource):
    def __init__(self, p: str, b: int = 32, hop: int = 10**7, **_):
        self._p, self._b, self._hop = p, b, hop
    def metadata(self): return {"kind": "audio.mic", "file": self._p, "bands": self._b}
    def subscribe(self) -> Iterator[EventPacket]:
        t = 0
        for _ in range(1000):
            for b in range(self._b):
                yield audio_band_event(t, b, m=0.1 * b)
            t += self._hop
