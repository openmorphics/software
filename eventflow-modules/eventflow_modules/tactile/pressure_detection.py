from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, XYToChannel
import json
from ..errors import TactileError

# Optional Rust acceleration for tactile processing
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore

def pressure_detection(
    source: Any,
    threshold: float = 0.1,
    window: str = "10 ms",
    spatial_resolution: int = 16,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Tactile pressure detection using event-based thresholding.

    This algorithm processes pressure sensor events from tactile arrays to detect
    contact pressure above specified thresholds. It uses spatial-temporal filtering
    to reduce noise and provide reliable pressure detection.

    Args:
        source: Input event source (tactile sensor data)
        threshold: Pressure threshold for detection (0.0-1.0)
        window: Temporal window for event integration
        spatial_resolution: Number of tactile sensors in array (NxN)
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured tactile pressure detection graph

    Raises:
        TactileError: If parameters are invalid or sensor configuration fails

    Example:
        # Basic pressure detection with default settings
        graph = pressure_detection(tactile_sensor, threshold=0.2)

        # High-resolution tactile sensing
        graph = pressure_detection(sensor, spatial_resolution=32, window="5 ms")
    """
    if not isinstance(threshold, (int, float)) or not (0.0 <= threshold <= 1.0):
        raise TactileError(f"Pressure threshold must be between 0.0 and 1.0, got {threshold}")

    if spatial_resolution <= 0 or spatial_resolution > 256:
        raise TactileError(f"Spatial resolution must be 1-256, got {spatial_resolution}")

    # Create EIR graph for tactile processing
    g = EIRGraph()

    # Map tactile sensor coordinates to channels
    # For tactile arrays, we use spatial coordinates (x,y) mapping
    xy_map = XYToChannel("xy", width=spatial_resolution, height=spatial_resolution).as_op()
    g.add_node("xy", xy_map)

    # Pressure thresholding with temporal integration
    pressure_threshold = EventFuse("pressure", window=window, min_count=int(threshold * 10)).as_op()
    g.add_node("pressure", pressure_threshold)

    # Connect coordinate mapping to pressure detection
    g.connect("xy", "ch", "pressure", "in")

    return g