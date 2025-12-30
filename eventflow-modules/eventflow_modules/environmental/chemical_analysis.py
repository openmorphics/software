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

def chemical_analysis(
    source: Any,
    analyte: str = "pH",
    range_min: float = 0.0,
    range_max: float = 14.0,
    calibration_offset: float = 0.0,
    window: str = "5 s",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Chemical analysis using event-based sensing for pH, conductivity, or concentration.

    This algorithm processes chemical sensor events to analyze solution properties
    such as pH levels, electrical conductivity, or chemical concentrations. It provides
    calibrated measurements with range validation and temporal smoothing.

    Args:
        source: Input sensor source (SAL URI or stream)
        analyte: Type of chemical analysis (pH, conductivity, concentration)
        range_min: Minimum valid measurement range
        range_max: Maximum valid measurement range
        calibration_offset: Calibration offset to apply
        window: Time window for averaging/filtering
        params: Additional parameters

    Returns:
        EIRGraph: Configured chemical analysis processing graph

    Raises:
        EnvironmentalError: For invalid parameters or sensor configuration
    """
    if range_min >= range_max:
        raise EnvironmentalError(f"Invalid range: min {range_min} >= max {range_max}")

    # Create base graph structure
    graph = EIRGraph(name=f"chemical_analysis_{analyte}")

    # Add input node
    graph.add_input("sensor_input", source)

    # Add calibration offset
    if calibration_offset != 0.0:
        calib_node = graph.add_node(
            "calibration",
            {
                "op": "offset",
                "offset": calibration_offset,
                "analyte": analyte
            }
        )
        graph.add_edge("sensor_input", calib_node)
        input_node = calib_node
    else:
        input_node = "sensor_input"

    # Add range validation
    range_node = graph.add_node(
        "range_validator",
        {
            "op": "clamp",
            "min": range_min,
            "max": range_max
        }
    )
    graph.add_edge(input_node, range_node)

    # Add temporal filtering
    filter_node = graph.add_node(
        "temporal_filter",
        {
            "op": "moving_average",
            "window": window
        }
    )
    graph.add_edge(range_node, filter_node)

    # Add output
    graph.add_output("analysis_output", filter_node)

    return graph