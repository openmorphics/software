from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine
import json
from ..errors import EnvironmentalError

# Optional Rust acceleration for environmental processing
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore

def gas_detection(
    source: Any,
    gas_type: str = "VOC",
    threshold_ppm: float = 50.0,
    window: str = "10 s",
    sensitivity: float = 1.0,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Gas detection using event-based chemical sensing.

    This algorithm processes gas sensor events to detect specific gases (VOC, CO, CO2, etc.)
    above specified concentration thresholds. It uses temporal filtering to reduce noise
    and provide reliable gas detection.

    Args:
        source: Input sensor source (SAL URI or stream)
        gas_type: Type of gas to detect (VOC, CO, CO2, NO2, etc.)
        threshold_ppm: Detection threshold in parts per million
        window: Time window for averaging/filtering
        sensitivity: Sensor sensitivity multiplier
        params: Additional parameters

    Returns:
        EIRGraph: Configured gas detection processing graph

    Raises:
        EnvironmentalError: For invalid parameters or sensor configuration
    """
    if threshold_ppm <= 0:
        raise EnvironmentalError(f"Invalid threshold_ppm: {threshold_ppm}, must be > 0")
    if sensitivity <= 0:
        raise EnvironmentalError(f"Invalid sensitivity: {sensitivity}, must be > 0")

    # Create base graph structure
    graph = EIRGraph(name=f"gas_detection_{gas_type}")

    # Add input node
    graph.add_input("sensor_input", source)

    # Add threshold detection
    threshold_node = graph.add_node(
        "threshold_detector",
        {
            "op": "threshold",
            "threshold": threshold_ppm * sensitivity,
            "gas_type": gas_type
        }
    )

    # Connect input to threshold detector
    graph.add_edge("sensor_input", threshold_node)

    # Add temporal filtering for noise reduction
    filter_node = graph.add_node(
        "temporal_filter",
        {
            "op": "moving_average",
            "window": window
        }
    )
    graph.add_edge(threshold_node, filter_node)

    # Add output
    graph.add_output("detection_output", filter_node)

    return graph