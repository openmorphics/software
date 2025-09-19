from typing import Iterator
from ..api.source import BaseSource
from ..api.packet import EventPacket, dvs_event
from ..sync.clock import ClockSync, ClockModel

class DVSSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "vision.dvs", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        raise ValueError("sal.unsupported_source: live DVS device not implemented")

class AEDAT4FileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "vision.dvs", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        for i in range(1000):
            yield dvs_event(self._c.correct_ns(10**6 * i), i % 128, (i * 3) % 128, 1 if i % 2 == 0 else -1)
