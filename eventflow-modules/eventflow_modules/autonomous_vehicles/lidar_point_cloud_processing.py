from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, XYToChannel
import json
from ..errors import AutonomousError

# Optional Rust acceleration for autonomous processing
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore

def lidar_point_cloud_processing(
    source: Any,
    obstacle_threshold: float = 0.5,
    ground_segmentation_window: str = "100 ms",
    max_range: float = 50.0,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    LiDAR point cloud processing for obstacle detection and ground segmentation.

    This algorithm processes 3D LiDAR point cloud events for real-time obstacle detection
    and ground plane segmentation. Uses event-based spatial-temporal filtering to identify
    obstacles and separate ground points from elevated objects.

    Args:
        source: Input LiDAR point cloud source (SAL URI or event stream)
        obstacle_threshold: Distance threshold for obstacle detection (meters)
        ground_segmentation_window: Temporal window for ground segmentation analysis
        max_range: Maximum detection range (meters)
        params: Additional configuration parameters

    Returns:
        EIRGraph: Configured processing graph for LiDAR point clouds

    Raises:
        AutonomousError: If parameters are invalid or LiDAR configuration fails
    """
    if not isinstance(obstacle_threshold, (int, float)) or not (0.0 <= obstacle_threshold <= 100.0):
        raise AutonomousError(f"Obstacle threshold must be between 0.0 and 100.0, got {obstacle_threshold}")

    if not isinstance(max_range, (int, float)) or not (1.0 <= max_range <= 200.0):
        raise AutonomousError(f"Max range must be between 1.0 and 200.0 meters, got {max_range}")

    # Create EIR graph for LiDAR processing
    graph = EIRGraph(name="lidar_point_cloud_processing")

    # Input node for LiDAR data
    graph.add_source("lidar_input", source)

    # Spatial filtering for obstacle detection
    obstacle_filter = graph.add_op(
        "spatial_filter",
        {
            "threshold": obstacle_threshold,
            "max_range": max_range,
        }
    )

    # Ground segmentation using temporal analysis
    ground_segment = graph.add_op(
        "ground_segmentation",
        {
            "window": ground_segmentation_window,
        }
    )

    # Connect nodes
    graph.connect("lidar_input", obstacle_filter)
    graph.connect(obstacle_filter, ground_segment)

    # Optional native acceleration
    if _ef_native_enabled():
        graph.enable_native_acceleration()

    return graph