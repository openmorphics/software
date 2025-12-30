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

def infrastructure_health(
    source: Any,
    vibration_threshold: float = 0.4,
    stress_threshold: float = 0.5,
    monitoring_window: str = "1 hour",
    sensor_points: int = 16,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Urban infrastructure health monitoring for smart cities.

    This algorithm processes data from structural health sensors (vibration, strain,
    temperature) to monitor bridges, buildings, and critical infrastructure. Uses
    event-based processing to detect structural anomalies and predict maintenance needs.

    Args:
        source: Input event source (structural sensor network data)
        vibration_threshold: Vibration anomaly threshold (0.0-1.0)
        stress_threshold: Structural stress threshold (0.0-1.0)
        monitoring_window: Time window for health trend analysis
        sensor_points: Number of sensor points on infrastructure
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured infrastructure health monitoring graph

    Raises:
        SmartCityError: If parameters are invalid or sensor configuration fails

    Example:
        # Bridge structural monitoring
        graph = infrastructure_health(bridge_sensors, vibration_threshold=0.6)

        # Building health monitoring
        graph = infrastructure_health(building_sensors, sensor_points=32, monitoring_window="24 hour")
    """
    if not isinstance(vibration_threshold, (int, float)) or not (0.0 <= vibration_threshold <= 1.0):
        raise SmartCityError(f"Invalid vibration_threshold: {vibration_threshold!r}, must be 0.0-1.0")

    if not isinstance(stress_threshold, (int, float)) or not (0.0 <= stress_threshold <= 1.0):
        raise SmartCityError(f"Invalid stress_threshold: {stress_threshold!r}, must be 0.0-1.0")

    if sensor_points <= 0 or sensor_points > 256:
        raise SmartCityError(f"Invalid sensor_points: {sensor_points}, must be 1-256")

    # Create EIR graph for infrastructure health monitoring
    g = EIRGraph()

    # Map sensor points to spatial coordinates
    sensor_map = XYToChannel("sensor_points", width=sensor_points, height=1).as_op()
    g.add_node("sensor_points", sensor_map)

    # Vibration monitoring for structural integrity
    vibration_monitor = EventFuse("vibration", window="10 min", min_count=int(vibration_threshold * 25)).as_op()
    g.add_node("vibration", vibration_monitor)

    # Structural stress monitoring
    stress_monitor = EventFuse("stress", window="30 min", min_count=int(stress_threshold * 15)).as_op()
    g.add_node("stress", stress_monitor)

    # Long-term health trend analysis
    health_trends = EventFuse("health_trends", window=monitoring_window, min_count=50).as_op()
    g.add_node("health_trends", health_trends)

    # Connect infrastructure monitoring pipeline
    g.connect("sensor_points", "ch", "vibration", "in")
    g.connect("sensor_points", "ch", "stress", "in")
    g.connect("vibration", "out", "health_trends", "a")
    g.connect("stress", "out", "health_trends", "b")

    return g