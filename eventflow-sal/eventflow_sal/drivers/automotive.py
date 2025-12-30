from typing import Iterator
from ..api.source import BaseSource
from ..api.packet import EventPacket, lidar_point_event, radar_detection_event
from ..sync.clock import ClockSync, ClockModel

class LiDARSource(BaseSource):
    def __init__(self, d: str = "front", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "lidar.cloud", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # This is a stub for a live source, so it yields nothing.
        return
        yield

class LiDARFileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "lidar.cloud", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic LiDAR point cloud file replay stub.

        For testing and examples, emit synthetic LiDAR events simulating
        3D point cloud data from a LiDAR sensor. Timestamps are corrected via ClockSync.

        Yields:
            Iterator[EventPacket]: Synthetic LiDAR point cloud events.
        """
        count = 1000
        t0_ns = 0
        dt_ns = 10_000  # 10 us between points in sensor time

        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)
            # Simulate 3D coordinates in meters
            x = (i % 100 - 50) * 0.1
            y = ((i // 100) % 50 - 25) * 0.1
            z = 2.0 + (i % 10) * 0.5  # Height from 2m to 7m
            intensity = min(255, (i % 20) * 12 + 50)  # Intensity 0-255

            # Create LiDAR point event
            pkt = lidar_point_event(ts_ns, x, y, z, intensity)
            self._watermark_ns = ts_ns
            yield pkt

class RadarSource(BaseSource):
    def __init__(self, d: str = "front", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "radar.detection", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # This is a stub for a live source, so it yields nothing.
        return
        yield

class RadarFileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "radar.detection", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic radar detection file replay stub.

        For testing and examples, emit synthetic radar detection events simulating
        range, azimuth, elevation, and velocity measurements. Timestamps are corrected via ClockSync.

        Yields:
            Iterator[EventPacket]: Synthetic radar detection events.
        """
        count = 500
        t0_ns = 0
        dt_ns = 50_000  # 50 us between detections in sensor time

        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)
            # Simulate radar detection parameters
            range_m = 5.0 + (i % 20) * 2.0  # Range from 5m to 45m
            azimuth_deg = (i % 60 - 30) * 1.0  # Azimuth -30° to +30°
            elevation_deg = (i % 10 - 5) * 0.5  # Elevation -2.5° to +2.5°
            velocity_mps = -20.0 + (i % 40) * 1.0  # Velocity -20 m/s to +20 m/s

            # Create radar detection event
            pkt = radar_detection_event(ts_ns, range_m, azimuth_deg, elevation_deg, velocity_mps)
            self._watermark_ns = ts_ns
            yield pkt