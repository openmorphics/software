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

def texture_analysis(
    source: Any,
    analysis_window: str = "50 ms",
    spatial_scale: int = 3,
    sensitivity: float = 0.8,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Tactile texture analysis for material recognition and surface classification.

    This algorithm analyzes spatio-temporal patterns in tactile sensor data to
    identify surface textures (roughness, smoothness, patterns). Uses event-based
    correlation and spatial-temporal filtering to extract texture features.

    Args:
        source: Input event source (tactile sensor data)
        analysis_window: Temporal window for texture analysis
        spatial_scale: Spatial scale for texture feature extraction (1-5)
        sensitivity: Sensitivity threshold for texture detection (0.0-1.0)
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured tactile texture analysis graph

    Raises:
        TactileError: If parameters are invalid or sensor configuration fails

    Example:
        # Texture analysis for material recognition
        graph = texture_analysis(tactile_sensor, spatial_scale=4, sensitivity=0.9)

        # Fine-grained texture analysis
        graph = texture_analysis(sensor, analysis_window="20 ms", spatial_scale=2)
    """
    if not isinstance(sensitivity, (int, float)) or not (0.0 <= sensitivity <= 1.0):
        raise TactileError(f"Sensitivity must be between 0.0 and 1.0, got {sensitivity}")

    if spatial_scale < 1 or spatial_scale > 5:
        raise TactileError(f"Spatial scale must be 1-5, got {spatial_scale}")

    # Create EIR graph for texture analysis
    g = EIRGraph()

    # Convert tactile coordinates to channels
    xy_map = XYToChannel("xy", width=16, height=16).as_op()  # Assume 16x16 tactile array
    g.add_node("xy", xy_map)

    # Multi-scale texture analysis using delayed correlations
    for scale in range(1, spatial_scale + 1):
        # Create correlation detector for this scale
        corr_name = f"texture_corr_{scale}"
        delay_name = f"texture_delay_{scale}"

        # Correlation with spatial offset
        correlation = EventFuse(corr_name, window=analysis_window, min_count=int(sensitivity * 5)).as_op()
        g.add_node(corr_name, correlation)

        # Delay line for temporal comparison
        delay = DelayLine(delay_name, delay=f"{scale * 5} ms").as_op()
        g.add_node(delay_name, delay)

        # Connect correlation and delay
        g.connect("xy", "ch", delay_name, "in")
        g.connect("xy", "ch", corr_name, "a")
        g.connect(delay_name, "out", corr_name, "b")

    return g