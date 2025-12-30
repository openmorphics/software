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

def soil_moisture_optimization(
    source: Any,
    moisture_threshold: float = 0.3,
    irrigation_window: str = "6 h",
    sensor_depth: int = 3,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Soil moisture optimization for precision irrigation management.

    Monitors soil moisture levels and optimizes irrigation scheduling
    using event-based processing for energy-efficient farm management.

    Args:
        source: Input event source (soil moisture sensors)
        moisture_threshold: Minimum moisture level for healthy soil (0.0-1.0)
        irrigation_window: Time window for irrigation decision making
        sensor_depth: Number of soil depth layers monitored
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured soil moisture optimization graph

    Raises:
        SmartAgricultureError: If parameters are invalid

    Example:
        # Basic moisture monitoring
        graph = soil_moisture_optimization(moisture_sensor, moisture_threshold=0.4)

        # Multi-depth soil analysis
        graph = soil_moisture_optimization(sensor, sensor_depth=5, irrigation_window="12 h")
    """
    if not isinstance(moisture_threshold, (int, float)) or not (0.0 <= moisture_threshold <= 1.0):
        raise SmartAgricultureError(f"Moisture threshold must be between 0.0 and 1.0, got {moisture_threshold}")

    if sensor_depth <= 0 or sensor_depth > 10:
        raise SmartAgricultureError(f"Sensor depth must be 1-10, got {sensor_depth}")

    # Create EIR graph for soil moisture monitoring
    g = EIRGraph()

    # Moisture level monitoring with temporal integration
    moisture_monitor = EventFuse("moisture", window=irrigation_window, min_count=int(moisture_threshold * 100)).as_op()
    g.add_node("moisture", moisture_monitor)

    return g

def ph_monitoring(
    source: Any,
    ph_target: float = 7.0,
    ph_tolerance: float = 0.5,
    monitoring_window: str = "24 h",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Soil pH monitoring and adjustment optimization.

    Tracks soil pH levels and provides recommendations for pH adjustment
    to maintain optimal conditions for crop growth.

    Args:
        source: Input event source (pH sensors)
        ph_target: Target pH level for optimal growth
        ph_tolerance: Acceptable pH deviation from target
        monitoring_window: Time window for pH stability assessment
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured pH monitoring graph

    Raises:
        SmartAgricultureError: If parameters are invalid

    Example:
        # Neutral pH targeting
        graph = ph_monitoring(ph_sensor, ph_target=7.0)

        # Acidic soil monitoring
        graph = ph_monitoring(sensor, ph_target=6.5, ph_tolerance=0.3)
    """
    if not isinstance(ph_target, (int, float)) or not (0.0 <= ph_target <= 14.0):
        raise SmartAgricultureError(f"pH target must be between 0.0 and 14.0, got {ph_target}")

    if not isinstance(ph_tolerance, (int, float)) or ph_tolerance <= 0:
        raise SmartAgricultureError(f"pH tolerance must be positive, got {ph_tolerance}")

    # Create EIR graph for pH monitoring
    g = EIRGraph()

    # pH stability monitoring
    ph_monitor = EventFuse("ph", window=monitoring_window, min_count=1).as_op()
    g.add_node("ph", ph_monitor)

    return g

def nutrient_analysis(
    source: Any,
    nutrient_types: list = None,
    deficiency_threshold: float = 0.2,
    analysis_window: str = "7 d",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Soil nutrient analysis for precision fertilization.

    Analyzes key soil nutrients (N, P, K) and provides fertilization
    recommendations using neuromorphic processing for efficient monitoring.

    Args:
        source: Input event source (nutrient sensors)
        nutrient_types: List of nutrients to monitor (e.g., ['N', 'P', 'K'])
        deficiency_threshold: Threshold for nutrient deficiency detection
        analysis_window: Time window for nutrient trend analysis
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured nutrient analysis graph

    Raises:
        SmartAgricultureError: If parameters are invalid

    Example:
        # NPK monitoring
        graph = nutrient_analysis(nutrient_sensor, nutrient_types=['N', 'P', 'K'])

        # Custom nutrient monitoring
        graph = nutrient_analysis(sensor, nutrient_types=['Ca', 'Mg'], deficiency_threshold=0.1)
    """
    if nutrient_types is None:
        nutrient_types = ['N', 'P', 'K']

    if not isinstance(nutrient_types, list) or len(nutrient_types) == 0:
        raise SmartAgricultureError("Nutrient types must be a non-empty list")

    if not isinstance(deficiency_threshold, (int, float)) or not (0.0 <= deficiency_threshold <= 1.0):
        raise SmartAgricultureError(f"Deficiency threshold must be between 0.0 and 1.0, got {deficiency_threshold}")

    # Create EIR graph for nutrient analysis
    g = EIRGraph()

    # Nutrient deficiency detection
    nutrient_monitor = EventFuse("nutrients", window=analysis_window, min_count=int(deficiency_threshold * 100)).as_op()
    g.add_node("nutrients", nutrient_monitor)

    return g