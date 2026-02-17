from typing import Iterator
from ..api.source import BaseSource
from ..api.packet import EventPacket, dvs_event
from ..sync.clock import ClockSync, ClockModel

class DVSSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "vision.dvs", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # This is a stub for a live source, so it yields nothing.
        return
        yield

class AEDAT4FileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "vision.dvs", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic AEDAT4 file replay stub.

        For testing and examples, emit a fixed number of synthetic DVS events without
        parsing the underlying file. Timestamps are corrected via ClockSync.

        Yields:
            Iterator[EventPacket]: 1000 synthetic DVS events.
        """
        count = 1000
        t0_ns = 0
        dt_ns = 1_000  # 1 us between events in sensor time
        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)
            x = i % 64
            y = (i // 64) % 64
            pol = i & 1
            pkt = dvs_event(ts_ns, x, y, pol)
            self._watermark_ns = ts_ns
            yield pkt
