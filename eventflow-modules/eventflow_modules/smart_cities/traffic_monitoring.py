from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, XYToChannel
import json
from ..errors import SmartCityError

# Optional Rust acceleration for smart city processing
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore

def traffic_monitoring(
    source: Any,
    detection_threshold: float = 0.3,
    congestion_window: str = "30 s",
    spatial_resolution: tuple[int, int] = (128, 128),
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Real-time traffic monitoring and congestion analysis for smart cities.

    This algorithm processes data from urban traffic sensors (cameras, inductive loops,
    radar) to detect vehicle movement patterns and identify congestion areas. Uses
    event-based temporal-spatial filtering to reduce data bandwidth while maintaining
    real-time traffic flow analysis.

    Args:
        source: Input event source (traffic camera or sensor data)
        detection_threshold: Motion detection sensitivity (0.0-1.0)
        congestion_window: Time window for congestion analysis
        spatial_resolution: Camera/sensor spatial resolution (width, height)
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured traffic monitoring graph

    Raises:
        SmartCityError: If parameters are invalid or sensor configuration fails

    Example:
        # Basic traffic monitoring
        graph = traffic_monitoring(traffic_camera, detection_threshold=0.4)

        # High-resolution urban monitoring
        graph = traffic_monitoring(sensor, spatial_resolution=(256, 256), congestion_window="60 s")
    """
    if not isinstance(detection_threshold, (int, float)) or not (0.0 <= detection_threshold <= 1.0):
        raise SmartCityError(f"Invalid detection_threshold: {detection_threshold!r}, must be 0.0-1.0")

    if not isinstance(spatial_resolution, tuple) or len(spatial_resolution) != 2:
        raise SmartCityError(f"Invalid spatial_resolution: {spatial_resolution!r}, must be (width, height) tuple")

    width, height = spatial_resolution
    if width <= 0 or height <= 0:
        raise SmartCityError(f"Invalid spatial_resolution dimensions: {width}x{height}, must be positive")

    # Create EIR graph for traffic monitoring
    g = EIRGraph()

    # Map traffic camera coordinates to channels
    xy_map = XYToChannel("xy", width=width, height=height).as_op()
    g.add_node("xy", xy_map)

    # Motion detection with temporal integration
    motion_detector = EventFuse("motion", window="10 ms", min_count=int(detection_threshold * 10)).as_op()
    g.add_node("motion", motion_detector)

    # Spatial pooling for bandwidth reduction
    spatial_pool = XYToChannel("spatial_pool", width=width // 4, height=height // 4).as_op()
    g.add_node("spatial_pool", spatial_pool)

    # Temporal aggregation for congestion analysis
    congestion_analyzer = EventFuse("congestion", window=congestion_window, min_count=5).as_op()
    g.add_node("congestion", congestion_analyzer)

    # Connect processing pipeline
    g.connect("xy", "ch", "motion", "in")
    g.connect("motion", "out", "spatial_pool", "xy")
    g.connect("spatial_pool", "ch", "congestion", "in")

    return g