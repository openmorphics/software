from typing import Iterator
from ..api.source import BaseSource
from ..api.packet import EventPacket, industrial_event
from ..sync.clock import ClockSync, ClockModel

class VibrationSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "industrial.vibration", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # This is a stub for a live source, so it yields nothing.
        return
        yield

class VibrationFileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "industrial.vibration", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic vibration sensor file replay stub.

        For testing and examples, emit synthetic vibration events simulating
        accelerometer readings from industrial equipment. Timestamps are corrected via ClockSync.

        Yields:
            Iterator[EventPacket]: Synthetic vibration sensor events.
        """
        count = 1000
        t0_ns = 0
        dt_ns = 1_000_000  # 1 ms between events in sensor time

        # Simulate vibration data from x, y, z axes
        axes = ["x", "y", "z"]
        axis_data = {axis: [] for axis in axes}

        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)

            # Generate synthetic vibration data
            for axis in axes:
                # Simulate normal operation with occasional anomalies
                base_amplitude = 0.1
                if i % 100 == 0:  # Occasional spike
                    amplitude = base_amplitude * (5.0 + (i % 3))
                else:
                    amplitude = base_amplitude + (i % 10) * 0.01

                # Create vibration event for each axis
                axis_idx = axes.index(axis)
                pkt = industrial_event(ts_ns, axis_idx, amplitude)
                self._watermark_ns = ts_ns
                yield pkt

class ProcessSensorSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "industrial.process", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # This is a stub for a live source, so it yields nothing.
        return
        yield

class ProcessSensorFileSource(BaseSource):
    def __init__(self, p: str, sensor_type: str = "temperature", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._sensor_type, self._c = p, sensor_type, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "industrial.process", "file": self._p, "sensor_type": self._sensor_type}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic process sensor file replay stub.

        For testing and examples, emit synthetic process sensor events for
        manufacturing monitoring. Timestamps are corrected via ClockSync.

        Yields:
            Iterator[EventPacket]: Synthetic process sensor events.
        """
        count = 500
        t0_ns = 0
        dt_ns = 10_000_000  # 10 ms between events in sensor time

        sensor_configs = {
            "temperature": {"base": 25.0, "range": 10.0, "unit": "celsius"},
            "pressure": {"base": 1.0, "range": 0.5, "unit": "bar"},
            "current": {"base": 2.0, "range": 1.0, "unit": "amps"},
            "speed": {"base": 1000.0, "range": 200.0, "unit": "rpm"},
            "force": {"base": 50.0, "range": 25.0, "unit": "newtons"}
        }

        config = sensor_configs.get(self._sensor_type, sensor_configs["temperature"])

        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)

            # Generate synthetic process data with controlled variations
            base_value = config["base"]
            variation = (i % 50) * config["range"] / 50.0

            # Occasional process anomalies
            if i % 200 == 0:
                value = base_value + variation + config["range"] * 2.0  # Anomaly spike
            else:
                value = base_value + variation

            # Create process sensor event
            pkt = industrial_event(ts_ns, 0, value)  # Single channel for process sensors
            self._watermark_ns = ts_ns
            yield pkt