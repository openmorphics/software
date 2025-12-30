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

def environmental_monitoring(
    source: Any,
    pollution_threshold: float = 0.6,
    noise_threshold: float = 0.7,
    monitoring_window: str = "15 min",
    sensor_count: int = 8,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Environmental monitoring for air quality and noise pollution in smart cities.

    This algorithm processes data from urban environmental sensors to monitor air
    quality (PM2.5, CO2, VOCs) and noise pollution levels. Uses event-based processing
    to efficiently detect pollution spikes and environmental anomalies.

    Args:
        source: Input event source (environmental sensor network data)
        pollution_threshold: Air quality threshold for alerts (0.0-1.0)
        noise_threshold: Noise pollution threshold for alerts (0.0-1.0)
        monitoring_window: Time window for environmental trend analysis
        sensor_count: Number of sensors in the network
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured environmental monitoring graph

    Raises:
        SmartCityError: If parameters are invalid or sensor configuration fails

    Example:
        # Basic air quality monitoring
        graph = environmental_monitoring(sensor_network, pollution_threshold=0.8)

        # Multi-sensor environmental monitoring
        graph = environmental_monitoring(sensors, sensor_count=16, monitoring_window="30 min")
    """
    if not isinstance(pollution_threshold, (int, float)) or not (0.0 <= pollution_threshold <= 1.0):
        raise SmartCityError(f"Invalid pollution_threshold: {pollution_threshold!r}, must be 0.0-1.0")

    if not isinstance(noise_threshold, (int, float)) or not (0.0 <= noise_threshold <= 1.0):
        raise SmartCityError(f"Invalid noise_threshold: {noise_threshold!r}, must be 0.0-1.0")

    if sensor_count <= 0 or sensor_count > 256:
        raise SmartCityError(f"Invalid sensor_count: {sensor_count}, must be 1-256")

    # Create EIR graph for environmental monitoring
    g = EIRGraph()

    # Map sensor network coordinates to channels (spatial distribution)
    sensor_map = XYToChannel("sensor_map", width=sensor_count, height=1).as_op()
    g.add_node("sensor_map", sensor_map)

    # Air quality monitoring (pollution detection)
    air_quality = EventFuse("air_quality", window="5 min", min_count=int(pollution_threshold * 15)).as_op()
    g.add_node("air_quality", air_quality)

    # Noise pollution monitoring
    noise_monitor = EventFuse("noise_pollution", window="1 min", min_count=int(noise_threshold * 20)).as_op()
    g.add_node("noise_pollution", noise_monitor)

    # Environmental trend analysis
    trend_analysis = EventFuse("environmental_trends", window=monitoring_window, min_count=30).as_op()
    g.add_node("environmental_trends", trend_analysis)

    # Connect environmental monitoring pipeline
    g.connect("sensor_map", "ch", "air_quality", "in")
    g.connect("sensor_map", "ch", "noise_pollution", "in")
    g.connect("air_quality", "out", "environmental_trends", "a")
    g.connect("noise_pollution", "out", "environmental_trends", "b")

    return g