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

def sensor_fusion(
    sources: Dict[str, Any],
    fusion_method: str = "kalman",
    temporal_alignment_window: str = "50 ms",
    confidence_threshold: float = 0.7,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Multi-sensor fusion for autonomous vehicle perception.

    Integrates data from multiple sensors (LiDAR, radar, camera, IMU) using
    event-based temporal alignment and probabilistic fusion methods.

    Args:
        sources: Dictionary mapping sensor types to their SAL URIs or event streams
                 (e.g., {"lidar": "av://lidar/front", "radar": "av://radar/rear"})
        fusion_method: Fusion algorithm ("kalman", "bayesian", "weighted_average")
        temporal_alignment_window: Maximum temporal offset for sensor alignment
        confidence_threshold: Minimum confidence score for fused detections
        params: Additional fusion parameters

    Returns:
        EIRGraph: Configured sensor fusion processing graph

    Raises:
        AutonomousError: If sensor configuration or fusion parameters are invalid
    """
    valid_methods = ["kalman", "bayesian", "weighted_average"]
    if fusion_method not in valid_methods:
        raise AutonomousError(f"Fusion method must be one of {valid_methods}, got {fusion_method}")

    if not isinstance(confidence_threshold, (int, float)) or not (0.0 <= confidence_threshold <= 1.0):
        raise AutonomousError(f"Confidence threshold must be between 0.0 and 1.0, got {confidence_threshold}")

    if not sources or not isinstance(sources, dict):
        raise AutonomousError("Sources must be a non-empty dictionary mapping sensor types to URIs")

    # Create EIR graph for sensor fusion
    graph = EIRGraph(name="sensor_fusion")

    # Input nodes for each sensor
    input_nodes = {}
    for sensor_type, source in sources.items():
        node_name = f"{sensor_type}_input"
        graph.add_source(node_name, source)
        input_nodes[sensor_type] = node_name

    # Temporal alignment operation
    temporal_align = graph.add_op(
        "temporal_alignment",
        {
            "window": temporal_alignment_window,
            "sensors": list(sources.keys()),
        }
    )

    # Sensor fusion operation
    fusion_op = graph.add_op(
        "sensor_fusion_op",
        {
            "method": fusion_method,
            "confidence_threshold": confidence_threshold,
        }
    )

    # Connect sensors to temporal alignment
    for node_name in input_nodes.values():
        graph.connect(node_name, temporal_align)

    # Connect alignment to fusion
    graph.connect(temporal_align, fusion_op)

    # Optional native acceleration
    if _ef_native_enabled():
        graph.enable_native_acceleration()

    return graph