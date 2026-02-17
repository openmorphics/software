from typing import Iterator
from ..api.source import BaseSource
from ..api.packet import EventPacket, tactile_event
from ..sync.clock import ClockSync, ClockModel

class TactileSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "tactile.array", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # This is a stub for a live source, so it yields nothing.
        return
        yield

class TactileFileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "tactile.array", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic tactile sensor file replay stub.

        For testing and examples, emit synthetic tactile events simulating
        pressure sensor readings from a tactile array. Timestamps are corrected via ClockSync.

        Yields:
            Iterator[EventPacket]: Synthetic tactile pressure events.
        """
        count = 500
        t0_ns = 0
        dt_ns = 2_000  # 2 us between events in sensor time

        # Simulate a 16x16 tactile array
        width, height = 16, 16

        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)
            x = i % width
            y = (i // width) % height

            # Simulate pressure value (0-255 range)
            pressure = min(255, (i % 10) * 25 + 50)

            # Create tactile event with pressure as value
            pkt = tactile_event(ts_ns, x, y, pressure)
            self._watermark_ns = ts_ns
            yield pkt