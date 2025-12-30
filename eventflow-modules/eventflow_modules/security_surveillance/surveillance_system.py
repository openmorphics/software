from __future__ import annotations
from typing import Optional, Dict, Any, List
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, XYToChannel, ShiftXY
import json
from ..errors import SecuritySurveillanceError

# Optional Rust acceleration for security surveillance processing
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore


def surveillance_system(
    source: Any,
    camera_count: int = 4,
    fusion_window: str = "1 s",
    coverage_overlap: float = 0.2,
    sensor_types: Optional[List[str]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Surveillance system integration using neuromorphic camera networks and sensor fusion.

    This algorithm processes multi-camera feeds and sensor data for comprehensive
    surveillance coverage. Implements energy-efficient distributed monitoring with
    overlapping camera fields and sensor fusion for enhanced detection accuracy.

    Args:
        source: Input event source (camera feeds, sensor networks)
        camera_count: Number of cameras in the network (1-16)
        fusion_window: Temporal window for sensor fusion
        coverage_overlap: Overlap factor between camera coverage areas (0.0-1.0)
        sensor_types: Optional list of sensor types to fuse ["camera", "motion", "thermal", "audio"]
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured surveillance system graph

    Raises:
        SecuritySurveillanceError: If parameters are invalid or configuration fails

    Example:
        # Basic surveillance system with 4 cameras
        graph = surveillance_system(camera_feeds, camera_count=4)

        # Overlapping coverage with sensor fusion
        graph = surveillance_system(sensors, camera_count=8, coverage_overlap=0.3)

        # Multi-modal sensor fusion
        graph = surveillance_system(data, sensor_types=["camera", "motion", "thermal"])
    """
    if camera_count <= 0 or camera_count > 16:
        raise SecuritySurveillanceError(f"Camera count must be 1-16, got {camera_count}")

    if not isinstance(coverage_overlap, (int, float)) or not (0.0 <= coverage_overlap <= 1.0):
        raise SecuritySurveillanceError(f"Coverage overlap must be between 0.0 and 1.0, got {coverage_overlap}")

    # Create EIR graph for surveillance system
    g = EIRGraph()

    # Camera network processing
    for i in range(camera_count):
        # Individual camera processing
        camera_process = XYToChannel(f"camera_{i}", width=640, height=480).as_op()
        g.add_node(f"camera_{i}", camera_process)

        # Camera-specific motion detection
        camera_motion = EventFuse(f"camera_motion_{i}", window="500 ms", min_count=3).as_op()
        g.add_node(f"camera_motion_{i}", camera_motion)

        # Connect camera processing to motion detection
        g.connect(f"camera_{i}", "ch", f"camera_motion_{i}", "a")

        # Coverage overlap compensation
        if coverage_overlap > 0.0:
            overlap_shift = ShiftXY(f"overlap_shift_{i}", dx=int(640 * coverage_overlap * (i % 2)),
                                   dy=int(480 * coverage_overlap * (i // 2)),
                                   width=640, height=480).as_op()
            g.add_node(f"overlap_shift_{i}", overlap_shift)
            g.connect(f"camera_motion_{i}", "out", f"overlap_shift_{i}", "in")

    # Sensor fusion across cameras
    fusion_integrate = EventFuse("fusion_integrate", window=fusion_window, min_count=camera_count // 2).as_op()
    g.add_node("fusion_integrate", fusion_integrate)

    # Network coordination
    network_coord = EventFuse("network_coord", window="2 s", min_count=2).as_op()
    g.add_node("network_coord", network_coord)

    # Connect camera outputs to fusion
    for i in range(camera_count):
        target_node = f"overlap_shift_{i}" if coverage_overlap > 0.0 else f"camera_motion_{i}"
        g.connect(target_node, "out", "fusion_integrate", "a")

    # Connect fusion to network coordination
    g.connect("fusion_integrate", "out", "network_coord", "a")

    # Temporal feedback for sustained surveillance
    surveillance_feedback = DelayLine("surveillance_feedback", delay="5 s").as_op()
    g.add_node("surveillance_feedback", surveillance_feedback)

    # Feedback loop for continuous monitoring
    g.connect("network_coord", "out", "surveillance_feedback", "in")
    g.connect("surveillance_feedback", "out", "fusion_integrate", "b")

    return g