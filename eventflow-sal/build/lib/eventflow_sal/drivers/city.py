from typing import Iterator
from ..api.source import BaseSource
from ..api.packet import EventPacket
from ..sync.clock import ClockSync, ClockModel

class TrafficCameraSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "city.traffic_camera", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic traffic camera source for smart cities.

        Simulates traffic camera events for vehicle detection and counting.
        Generates events representing vehicle movements at intersections.

        Yields:
            Iterator[EventPacket]: Synthetic traffic detection events.
        """
        return
        yield

class NoiseSensorSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "city.noise_sensor", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic noise pollution sensor for urban monitoring.

        Simulates noise level measurements from urban acoustic sensors.
        Generates events representing decibel levels and noise patterns.

        Yields:
            Iterator[EventPacket]: Synthetic noise pollution events.
        """
        return
        yield

class PollutionSensorSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "city.pollution_sensor", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic air pollution sensor for environmental monitoring.

        Simulates air quality measurements (PM2.5, CO2, VOCs) from urban sensors.
        Generates events representing pollution levels and air quality metrics.

        Yields:
            Iterator[EventPacket]: Synthetic pollution monitoring events.
        """
        return
        yield

class CrowdSensorSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "city.crowd_sensor", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic crowd density sensor for urban mobility tracking.

        Simulates crowd density measurements from urban cameras and motion sensors.
        Generates events representing people count and movement patterns.

        Yields:
            Iterator[EventPacket]: Synthetic crowd analysis events.
        """
        return
        yield

class InfrastructureSensorSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "city.infrastructure_sensor", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic infrastructure health sensor for structural monitoring.

        Simulates vibration and stress measurements from structural health sensors.
        Generates events representing bridge/building integrity and maintenance alerts.

        Yields:
            Iterator[EventPacket]: Synthetic infrastructure health events.
        """
        return
        yield

class CitySensorFileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
        # Parse sensor type from file extension or query params
        if "traffic" in p.lower():
            self._sensor_type = "traffic"
        elif "noise" in p.lower():
            self._sensor_type = "noise"
        elif "pollution" in p.lower():
            self._sensor_type = "pollution"
        elif "crowd" in p.lower():
            self._sensor_type = "crowd"
        elif "infrastructure" in p.lower():
            self._sensor_type = "infrastructure"
        else:
            self._sensor_type = "generic"

    def metadata(self): return {"kind": f"city.{self._sensor_type}_file", "file": self._p}

    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic city sensor file replay for testing and examples.

        Simulates urban IoT sensor data replay from recorded files.
        Generates synthetic events based on sensor type and file content.

        Yields:
            Iterator[EventPacket]: Synthetic city sensor events.
        """
        count = 1000
        t0_ns = 0
        dt_ns = 100_000_000  # 100ms between events in sensor time

        # Simulate different sensor types with appropriate event patterns
        if self._sensor_type == "traffic":
            # Traffic events: vehicle detections
            for i in range(count):
                ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)
                # Simulate vehicle position and speed
                x = i % 10  # lane position
                y = (i // 10) % 4  # direction
                speed = min(255, 50 + (i % 50))  # speed in km/h encoded as byte
                pkt = EventPacket(ts_ns, 0, float(speed), {"sensor_type": "traffic", "x": x, "y": y, "speed": speed})
                self._watermark_ns = ts_ns
                yield pkt

        elif self._sensor_type == "noise":
            # Noise events: decibel levels
            for i in range(count):
                ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)
                # Simulate noise level variations
                x = i % 8  # sensor position
                y = 0
                db_level = min(255, 40 + (i % 60))  # decibel level encoded as byte
                pkt = EventPacket(ts_ns, 0, float(db_level), {"sensor_type": "noise", "x": x, "y": y, "db_level": db_level})
                self._watermark_ns = ts_ns
                yield pkt

        elif self._sensor_type == "pollution":
            # Pollution events: air quality metrics
            for i in range(count):
                ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)
                # Simulate pollution measurements
                x = i % 6  # sensor position
                y = 0
                pm25 = min(255, 10 + (i % 100))  # PM2.5 level encoded as byte
                pkt = EventPacket(ts_ns, 0, float(pm25), {"sensor_type": "pollution", "x": x, "y": y, "pm25": pm25})
                self._watermark_ns = ts_ns
                yield pkt

        elif self._sensor_type == "crowd":
            # Crowd events: people density
            for i in range(count):
                ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)
                # Simulate crowd density
                x = i % 16  # spatial position
                y = (i // 16) % 16
                density = min(255, (i % 50) * 5)  # crowd density encoded as byte
                pkt = EventPacket(ts_ns, 0, float(density), {"sensor_type": "crowd", "x": x, "y": y, "density": density})
                self._watermark_ns = ts_ns
                yield pkt

        elif self._sensor_type == "infrastructure":
            # Infrastructure events: structural measurements
            for i in range(count):
                ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)
                # Simulate vibration/stress measurements
                x = i % 16  # sensor point
                y = 0
                vibration = min(255, 5 + (i % 50))  # vibration amplitude
                pkt = EventPacket(ts_ns, 0, float(vibration), {"sensor_type": "infrastructure", "x": x, "y": y, "vibration": vibration})
                self._watermark_ns = ts_ns
                yield pkt

        else:
            # Generic city sensor events
            for i in range(count):
                ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)
                x = i % 32
                y = (i // 32) % 32
                value = min(255, i % 256)
                pkt = EventPacket(ts_ns, 0, float(value), {"sensor_type": "generic", "x": x, "y": y, "value": value})
                self._watermark_ns = ts_ns
                yield pkt