from typing import Iterator
from ..api.source import BaseSource
from ..api.packet import EventPacket
from ..sync.clock import ClockSync, ClockModel

def motion_detector_event(t, zone, intensity, u: str = "dimensionless") -> EventPacket:
    return EventPacket(t, 0, float(intensity), {"unit": u, "sensor_type": "motion_detector", "zone": zone, "intensity": intensity})

def camera_motion_event(t, x, y, width, height, u: str = "pixels") -> EventPacket:
    return EventPacket(t, 0, 1.0, {"unit": u, "sensor_type": "camera", "x": x, "y": y, "width": width, "height": height, "motion_detected": True})

def perimeter_breach_event(t, zone, breach_intensity, breach_type, u: str = "dimensionless") -> EventPacket:
    return EventPacket(t, 0, float(breach_intensity), {"unit": u, "sensor_type": "perimeter_sensor", "zone": zone, "breach_type": breach_type, "intensity": breach_intensity})

class MotionDetectorSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "security.motion_detector", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # This is a stub for a live motion detector source, so it yields nothing.
        return
        yield

class MotionDetectorFileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "security.motion_detector", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic motion detector file replay stub.

        For testing and examples, emit synthetic motion detection events simulating
        PIR sensor readings. Timestamps are corrected via ClockSync.

        Yields:
            Iterator[EventPacket]: Synthetic motion detection events.
        """
        count = 200
        t0_ns = 0
        dt_ns = 5_000_000  # 5 ms between potential motion events in sensor time

        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)

            # Simulate motion detection with varying intensity (0-255 range)
            motion_intensity = min(255, (i % 20) * 12 + 10)

            # Only emit events when motion is detected above threshold
            if motion_intensity > 20:
                pkt = motion_detector_event(ts_ns, i % 4, motion_intensity)
                self._watermark_ns = ts_ns
                yield pkt

class CameraSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "security.camera", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # This is a stub for a live camera source, so it yields nothing.
        return
        yield

class CameraFileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "security.camera", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic camera file replay stub.

        For testing and examples, emit synthetic camera events simulating
        video frame processing with motion detection. Timestamps are corrected via ClockSync.

        Yields:
            Iterator[EventPacket]: Synthetic camera motion detection events.
        """
        count = 100
        t0_ns = 0
        dt_ns = 33_333_333  # ~30 fps in nanoseconds

        # Camera resolution simulation
        width, height = 640, 480

        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)

            # Simulate motion detection coordinates
            if i % 10 == 0:  # Motion detected every 10 frames
                x = (i * 37) % width
                y = (i * 23) % height

                pkt = camera_motion_event(ts_ns, x, y, width, height)
                self._watermark_ns = ts_ns
                yield pkt

class PerimeterSensorSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "security.perimeter_sensor", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # This is a stub for a live perimeter sensor source, so it yields nothing.
        return
        yield

class PerimeterSensorFileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "security.perimeter_sensor", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic perimeter sensor file replay stub.

        For testing and examples, emit synthetic perimeter breach events simulating
        fence sensors, infrared beams, or ground sensors. Timestamps are corrected via ClockSync.

        Yields:
            Iterator[EventPacket]: Synthetic perimeter breach events.
        """
        count = 50
        t0_ns = 0
        dt_ns = 100_000_000  # 100 ms between potential perimeter events in sensor time

        # Perimeter zones
        zones = ["north_fence", "south_fence", "east_fence", "west_fence", "main_gate"]

        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)

            # Simulate perimeter breaches with varying severity
            breach_intensity = min(100, (i % 15) * 7 + 5)

            # Only emit events when breach is detected above threshold
            if breach_intensity > 15:
                zone = zones[i % len(zones)]
                breach_type = "intrusion" if breach_intensity > 50 else "disturbance"

                pkt = perimeter_breach_event(ts_ns, zone, breach_intensity, breach_type)
                self._watermark_ns = ts_ns
                yield pkt