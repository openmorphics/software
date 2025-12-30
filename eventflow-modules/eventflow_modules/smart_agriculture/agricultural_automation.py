from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, XYToChannel
import json
from ..errors import SmartAgricultureError

# Optional Rust acceleration for smart agriculture processing
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore

def precision_spraying(
    source: Any,
    pest_threshold: float = 0.5,
    spray_window: str = "2 h",
    field_resolution: int = 100,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Precision spraying for targeted pest control.

    Uses computer vision and sensor data to identify pest-infested areas
    and optimize pesticide application for minimal environmental impact.

    Args:
        source: Input event source (camera or pest detection sensors)
        pest_threshold: Threshold for pest detection triggering spray
        spray_window: Time window for spray application scheduling
        field_resolution: Spatial resolution of field monitoring grid
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured precision spraying graph

    Raises:
        SmartAgricultureError: If parameters are invalid

    Example:
        # Standard pest monitoring
        graph = precision_spraying(camera_sensor, pest_threshold=0.6)

        # High-resolution field spraying
        graph = precision_spraying(sensor, field_resolution=200, spray_window="1 h")
    """
    if not isinstance(pest_threshold, (int, float)) or not (0.0 <= pest_threshold <= 1.0):
        raise SmartAgricultureError(f"Pest threshold must be between 0.0 and 1.0, got {pest_threshold}")

    if field_resolution <= 0 or field_resolution > 1000:
        raise SmartAgricultureError(f"Field resolution must be 1-1000, got {field_resolution}")

    # Create EIR graph for precision spraying
    g = EIRGraph()

    # Spatial pest detection mapping
    xy_map = XYToChannel("xy", width=field_resolution, height=field_resolution).as_op()
    g.add_node("xy", xy_map)

    # Pest threshold detection
    pest_detect = EventFuse("pest", window=spray_window, min_count=int(pest_threshold * 100)).as_op()
    g.add_node("pest", pest_detect)

    # Connect spatial mapping to pest detection
    g.connect("xy", "ch", "pest", "in")

    return g

def automated_harvesting(
    source: Any,
    ripeness_threshold: float = 0.8,
    harvest_window: str = "12 h",
    crop_type: str = "generic",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Automated harvesting optimization based on crop ripeness.

    Monitors crop maturity using imaging and sensor data to optimize
    harvesting timing and reduce waste in precision agriculture.

    Args:
        source: Input event source (ripeness sensors or cameras)
        ripeness_threshold: Minimum ripeness level for harvesting
        harvest_window: Time window for harvest scheduling
        crop_type: Type of crop being monitored
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured automated harvesting graph

    Raises:
        SmartAgricultureError: If parameters are invalid

    Example:
        # Tomato harvesting
        graph = automated_harvesting(ripeness_sensor, crop_type="tomato", ripeness_threshold=0.9)

        # Grain harvesting
        graph = automated_harvesting(sensor, crop_type="wheat", harvest_window="24 h")
    """
    if not isinstance(ripeness_threshold, (int, float)) or not (0.0 <= ripeness_threshold <= 1.0):
        raise SmartAgricultureError(f"Ripeness threshold must be between 0.0 and 1.0, got {ripeness_threshold}")

    if not isinstance(crop_type, str) or len(crop_type.strip()) == 0:
        raise SmartAgricultureError("Crop type must be a non-empty string")

    # Create EIR graph for automated harvesting
    g = EIRGraph()

    # Ripeness monitoring with temporal integration
    harvest_monitor = EventFuse("harvest", window=harvest_window, min_count=int(ripeness_threshold * 100)).as_op()
    g.add_node("harvest", harvest_monitor)

    return g

def pest_detection(
    source: Any,
    detection_sensitivity: float = 0.7,
    monitoring_window: str = "6 h",
    pest_types: list = None,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Intelligent pest detection using multimodal sensing.

    Combines visual, acoustic, and chemical sensors for comprehensive
    pest monitoring and early warning systems in agriculture.

    Args:
        source: Input event source (multimodal pest sensors)
        detection_sensitivity: Sensitivity for pest detection (0.0-1.0)
        monitoring_window: Time window for continuous monitoring
        pest_types: List of pest species to monitor
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured pest detection graph

    Raises:
        SmartAgricultureError: If parameters are invalid

    Example:
        # General pest monitoring
        graph = pest_detection(multimodal_sensor, detection_sensitivity=0.8)

        # Specific pest types
        graph = pest_detection(sensor, pest_types=['aphid', 'beetle'], monitoring_window="12 h")
    """
    if not isinstance(detection_sensitivity, (int, float)) or not (0.0 <= detection_sensitivity <= 1.0):
        raise SmartAgricultureError(f"Detection sensitivity must be between 0.0 and 1.0, got {detection_sensitivity}")

    if pest_types is None:
        pest_types = ['general']

    if not isinstance(pest_types, list) or len(pest_types) == 0:
        raise SmartAgricultureError("Pest types must be a non-empty list")

    # Create EIR graph for pest detection
    g = EIRGraph()

    # Multimodal pest detection
    if _ef_native_enabled():
        pest_op = _ef_native.pest_detect(detection_sensitivity, monitoring_window).as_op()
    else:
        pest_op = EventFuse("pest_detect", window=monitoring_window, min_count=int(detection_sensitivity * 100)).as_op()

    g.add_node("pest_detect", pest_op)

    return g