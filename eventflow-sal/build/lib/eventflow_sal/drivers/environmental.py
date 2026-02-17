from typing import Iterator
from ..api.source import BaseSource
from ..api.packet import EventPacket, environmental_event
from ..sync.clock import ClockSync, ClockModel

class EnvironmentalSource(BaseSource):
    def __init__(self, sensor_type: str = "gas", d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._sensor_type, self._d = sensor_type, d
        self._c = c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "environmental.sensor", "sensor_type": self._sensor_type, "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # This is a stub for a live source, so it yields nothing.
        return
        yield

class EnvironmentalFileSource(BaseSource):
    def __init__(self, p: str, sensor_type: str = "gas", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._sensor_type, self._c = p, sensor_type, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "environmental.sensor", "sensor_type": self._sensor_type, "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic environmental sensor file replay stub.

        For testing and examples, emit synthetic environmental events simulating
        gas, chemical, or air quality sensor readings. Timestamps are corrected via ClockSync.

        Yields:
            Iterator[EventPacket]: Synthetic environmental sensor events.
        """
        count = 500
        t0_ns = 0
        dt_ns = 1_000_000_000  # 1 second between events in sensor time

        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)

            # Simulate different sensor types
            if self._sensor_type == "gas":
                # VOC concentration in ppm
                concentration = min(500.0, (i % 50) * 10 + 20)
                sensor_type_meta = "VOC"
            elif self._sensor_type == "chemical":
                # pH level
                concentration = 7.0 + (i % 20 - 10) * 0.1
                sensor_type_meta = "pH"
            elif self._sensor_type == "air_quality":
                # PM2.5 in µg/m³
                concentration = min(100.0, (i % 30) * 3 + 10)
                sensor_type_meta = "PM2.5"
            else:
                concentration = float(i % 100)
                sensor_type_meta = self._sensor_type

            # Create environmental event
            pkt = environmental_event(ts_ns, sensor_type_meta, concentration)
            self._watermark_ns = ts_ns
            yield pkt