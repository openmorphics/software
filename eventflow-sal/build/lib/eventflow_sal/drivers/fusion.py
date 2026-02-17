from typing import Iterator, List, Any
from ..api.source import BaseSource
from ..api.packet import EventPacket
from ..sync.clock import ClockSync, ClockModel

class FusionSource(BaseSource):
    def __init__(self, sources: List[str] = None, fusion_type: str = "kalman", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._sources = sources or []
        self._fusion_type = fusion_type
        self._c = c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "fusion.stream", "fusion_type": self._fusion_type, "sources": self._sources}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Multi-modal fusion source that combines data from multiple sensor streams.

        For testing and examples, emit synthetic fused sensor events representing
        combined vision, audio, IMU, and other sensor data. Timestamps are corrected via ClockSync.

        Yields:
            Iterator[EventPacket]: Synthetic fused sensor events.
        """
        count = 1000
        t0_ns = 0
        dt_ns = 1_000_000  # 1 ms between fusion events

        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)

            # Simulate fused sensor data (multi-modal features)
            # Combine different sensor modalities into unified representation
            fused_value = {
                "vision_features": [0.1 * (i % 10), 0.2 * (i % 5)],
                "audio_features": [0.3 * (i % 8), 0.4 * (i % 6)],
                "imu_features": [0.5 * (i % 12), 0.6 * (i % 7)],
                "confidence": min(0.95, 0.5 + 0.01 * i),
                "fusion_timestamp": ts_ns
            }

            # Create fusion event with multi-modal data
            pkt = EventPacket(ts_ns, 0, 0.0, {"fusion_data": fused_value, "unit": "fusion"})
            self._watermark_ns = ts_ns
            yield pkt

class FusionFileSource(BaseSource):
    def __init__(self, p: str, fusion_type: str = "kalman", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p = p
        self._fusion_type = fusion_type
        self._c = c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "fusion.stream", "fusion_type": self._fusion_type, "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Multi-modal fusion file replay source.

        For testing and examples, simulate loading fused sensor data from file
        and emitting events with appropriate temporal alignment.

        Yields:
            Iterator[EventPacket]: Replayed fused sensor events.
        """
        # Simulate file replay with synthetic fusion data
        count = 500
        t0_ns = 0
        dt_ns = 2_000_000  # 2 ms between events

        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)

            # Simulate loaded fusion data
            fused_data = {
                "scene_context": f"scene_{i % 3}",
                "object_count": i % 5 + 1,
                "activity_detected": (i % 10) > 7,
                "sensor_reliability": [0.9, 0.85, 0.95],  # vision, audio, IMU
                "fusion_quality": min(1.0, 0.7 + 0.005 * i)
            }

            pkt = EventPacket(ts_ns, 0, 0.0, {"fusion_data": fused_data, "unit": "fusion"})
            self._watermark_ns = ts_ns
            yield pkt