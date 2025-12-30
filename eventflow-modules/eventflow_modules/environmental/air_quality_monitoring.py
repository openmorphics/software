from __future__ import annotations
from typing import Optional, Dict, Any, List
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

def air_quality_monitoring(
    sources: List[Any],
    pollutants: List[str] = ["PM2.5", "PM10", "NO2", "CO", "O3"],
    thresholds: Dict[str, float] = None,
    monitoring_window: str = "1 hour",
    alert_level: str = "moderate",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Air quality monitoring using multi-sensor environmental data fusion.

    This algorithm combines data from multiple environmental sensors to provide
    comprehensive air quality assessment including particulate matter, gases,
    and atmospheric conditions. It computes air quality indices and alerts.

    Args:
        sources: List of input sensor sources (SAL URIs or streams)
        pollutants: List of pollutants to monitor
        thresholds: Alert thresholds for each pollutant
        monitoring_window: Time window for averaging measurements
        alert_level: Alert sensitivity level (low, moderate, high)
        params: Additional parameters

    Returns:
        EIRGraph: Configured air quality monitoring processing graph

    Raises:
        EnvironmentalError: For invalid parameters or sensor configuration
    """
    if not sources:
        raise EnvironmentalError("At least one sensor source required")

    if thresholds is None:
        # Default EPA thresholds
        thresholds = {
            "PM2.5": 35.0,  # 24-hour average µg/m³
            "PM10": 150.0,  # 24-hour average µg/m³
            "NO2": 100.0,   # 1-hour average ppb
            "CO": 35.0,     # 1-hour average ppm
            "O3": 70.0      # 1-hour average ppb
        }

    # Create base graph structure
    graph = EIRGraph(name="air_quality_monitoring")

    # Add input nodes for each source
    input_nodes = []
    for i, source in enumerate(sources):
        input_name = f"sensor_input_{i}"
        graph.add_input(input_name, source)
        input_nodes.append(input_name)

    # Add pollutant-specific processing nodes
    pollutant_nodes = []
    for pollutant in pollutants:
        threshold = thresholds.get(pollutant, 50.0)  # Default threshold

        # Threshold detection for this pollutant
        thresh_node = graph.add_node(
            f"{pollutant}_threshold",
            {
                "op": "threshold",
                "threshold": threshold,
                "pollutant": pollutant,
                "alert_level": alert_level
            }
        )

        # Temporal averaging
        avg_node = graph.add_node(
            f"{pollutant}_average",
            {
                "op": "moving_average",
                "window": monitoring_window,
                "pollutant": pollutant
            }
        )

        graph.add_edge(thresh_node, avg_node)
        pollutant_nodes.append(avg_node)

        # Connect relevant sensor inputs (simplified - in practice would need sensor type mapping)
        for input_node in input_nodes:
            graph.add_edge(input_node, thresh_node)

    # Add air quality index computation
    aqi_node = graph.add_node(
        "air_quality_index",
        {
            "op": "aggregate_aqi",
            "pollutants": pollutants,
            "weights": {p: 1.0 for p in pollutants}  # Equal weighting
        }
    )

    for node in pollutant_nodes:
        graph.add_edge(node, aqi_node)

    # Add alert generation
    alert_node = graph.add_node(
        "alert_generator",
        {
            "op": "alert",
            "thresholds": thresholds,
            "alert_level": alert_level
        }
    )
    graph.add_edge(aqi_node, alert_node)

    # Add output
    graph.add_output("monitoring_output", alert_node)

    return graph