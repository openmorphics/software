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

def crowd_analysis(
    source: Any,
    density_threshold: float = 0.5,
    analysis_window: str = "30 s",
    spatial_resolution: tuple[int, int] = (64, 64),
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Crowd analysis and urban mobility tracking for smart cities.

    This algorithm processes data from urban cameras and sensors to analyze crowd
    density, movement patterns, and mobility flows. Uses event-based processing
    to efficiently track people movement and detect crowd anomalies in real-time.

    Args:
        source: Input event source (urban camera or motion sensor data)
        density_threshold: Crowd density threshold for alerting (0.0-1.0)
        analysis_window: Time window for mobility analysis
        spatial_resolution: Camera/sensor spatial resolution (width, height)
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured crowd analysis graph

    Raises:
        SmartCityError: If parameters are invalid or sensor configuration fails

    Example:
        # Basic crowd monitoring
        graph = crowd_analysis(urban_camera, density_threshold=0.7)

        # High-resolution urban mobility tracking
        graph = crowd_analysis(sensor, spatial_resolution=(128, 128), analysis_window="60 s")
    """
    if not isinstance(density_threshold, (int, float)) or not (0.0 <= density_threshold <= 1.0):
        raise SmartCityError(f"Invalid density_threshold: {density_threshold!r}, must be 0.0-1.0")

    if not isinstance(spatial_resolution, tuple) or len(spatial_resolution) != 2:
        raise SmartCityError(f"Invalid spatial_resolution: {spatial_resolution!r}, must be (width, height) tuple")

    width, height = spatial_resolution
    if width <= 0 or height <= 0:
        raise SmartCityError(f"Invalid spatial_resolution dimensions: {width}x{height}, must be positive")

    # Create EIR graph for crowd analysis
    g = EIRGraph()

    # Map urban camera coordinates to channels
    xy_map = XYToChannel("xy", width=width, height=height).as_op()
    g.add_node("xy", xy_map)

    # Motion detection for crowd tracking
    crowd_motion = EventFuse("crowd_motion", window="5 ms", min_count=int(density_threshold * 8)).as_op()
    g.add_node("crowd_motion", crowd_motion)

    # Spatial clustering for crowd density analysis
    density_cluster = XYToChannel("density", width=width // 8, height=height // 8).as_op()
    g.add_node("density", density_cluster)

    # Temporal analysis for mobility patterns
    mobility_pattern = EventFuse("mobility", window=analysis_window, min_count=10).as_op()
    g.add_node("mobility", mobility_pattern)

    # Connect crowd analysis pipeline
    g.connect("xy", "ch", "crowd_motion", "in")
    g.connect("crowd_motion", "out", "density", "xy")
    g.connect("density", "ch", "mobility", "in")

    return g