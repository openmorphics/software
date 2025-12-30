from __future__ import annotations
from typing import Optional, Dict, Any
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


def intrusion_detection(
    source: Any,
    motion_threshold: float = 0.5,
    anomaly_window: str = "1 s",
    spatial_resolution: int = 64,
    perimeter_zones: Optional[list] = None,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Intrusion detection using neuromorphic motion tracking and anomaly detection.

    This algorithm processes security sensor events (motion detectors, cameras) to detect
    intrusions by analyzing motion patterns and identifying anomalous behavior. Uses
    spatial-temporal event processing for energy-efficient perimeter monitoring.

    Args:
        source: Input event source (security sensors - motion detectors, cameras)
        motion_threshold: Threshold for motion detection sensitivity (0.0-1.0)
        anomaly_window: Temporal window for anomaly detection
        spatial_resolution: Spatial resolution for perimeter grid (NxN)
        perimeter_zones: Optional list of sensitive perimeter zones [(x1,y1,x2,y2), ...]
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured intrusion detection graph

    Raises:
        SecuritySurveillanceError: If parameters are invalid or sensor configuration fails

    Example:
        # Basic intrusion detection with default settings
        graph = intrusion_detection(motion_sensor, motion_threshold=0.3)

        # High-resolution perimeter monitoring
        graph = intrusion_detection(camera_feed, spatial_resolution=128,
                                  perimeter_zones=[(0,0,32,32), (96,96,128,128)])

        # Sensitive area monitoring with short anomaly window
        graph = intrusion_detection(sensor, anomaly_window="500 ms")
    """
    if not isinstance(motion_threshold, (int, float)) or not (0.0 <= motion_threshold <= 1.0):
        raise SecuritySurveillanceError(f"Motion threshold must be between 0.0 and 1.0, got {motion_threshold}")

    if spatial_resolution <= 0 or spatial_resolution > 512:
        raise SecuritySurveillanceError(f"Spatial resolution must be 1-512, got {spatial_resolution}")

    # Create EIR graph for intrusion detection
    g = EIRGraph()

    # Spatial coordinate mapping for perimeter grid
    xy_map = XYToChannel("spatial_map", width=spatial_resolution, height=spatial_resolution).as_op()
    g.add_node("spatial_map", xy_map)

    # Motion pattern detection using event fusion
    motion_detect = EventFuse("motion_pattern", window=anomaly_window, min_count=int(motion_threshold * 5)).as_op()
    g.add_node("motion_pattern", motion_detect)

    # Anomaly detection with temporal correlation
    anomaly_detect = EventFuse("anomaly_detect", window=anomaly_window, min_count=2).as_op()
    g.add_node("anomaly_detect", anomaly_detect)

    # Temporal delay for motion history tracking
    motion_delay = DelayLine("motion_history", delay="100 ms").as_op()
    g.add_node("motion_history", motion_delay)

    # Connect spatial mapping to motion detection
    g.connect("spatial_map", "ch", "motion_pattern", "a")

    # Connect motion history to anomaly detection
    g.connect("motion_history", "out", "anomaly_detect", "a")

    # Cross-connect motion patterns to anomaly detection for correlation
    g.connect("motion_pattern", "out", "anomaly_detect", "b")

    # Feedback motion patterns to history tracking
    g.connect("motion_pattern", "out", "motion_history", "in")

    # If perimeter zones specified, add zone-specific processing
    if perimeter_zones:
        for i, zone in enumerate(perimeter_zones):
            if len(zone) != 4:
                raise SecuritySurveillanceError(f"Perimeter zone {i} must be (x1,y1,x2,y2), got {zone}")

            # Zone-specific motion detection
            zone_detect = EventFuse(f"zone_{i}_detect", window="200 ms", min_count=1).as_op()
            g.add_node(f"zone_{i}_detect", zone_detect)

            # Connect zone detection to main anomaly detection
            g.connect(f"zone_{i}_detect", "out", "anomaly_detect", "a")

    return g