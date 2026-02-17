from __future__ import annotations
from typing import Optional, Dict, Any, List
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, LIFNeuron
import json
from ..errors import IndustrialError

# Optional Rust acceleration for industrial processing
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore

def predictive_maintenance(
    source: Any,
    equipment_type: str = "generic",
    failure_threshold: float = 0.8,
    health_window: str = "1 hour",
    anomaly_sensitivity: float = 0.6,
    maintenance_schedule: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Predictive maintenance using anomaly detection and equipment health monitoring.

    This algorithm analyzes sensor data to predict equipment failures before they occur,
    using neuromorphic processing for real-time anomaly detection and health assessment.
    It supports different equipment types with configurable failure patterns.

    Args:
        source: Input event source (equipment sensor data)
        equipment_type: Type of equipment ("motor", "pump", "bearing", "generic")
        failure_threshold: Health score threshold for failure prediction (0.0-1.0)
        health_window: Time window for health assessment
        anomaly_sensitivity: Sensitivity for anomaly detection (0.0-1.0)
        maintenance_schedule: Scheduled maintenance intervals
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured predictive maintenance graph

    Raises:
        IndustrialError: If parameters are invalid or equipment configuration fails

    Example:
        # Motor predictive maintenance
        graph = predictive_maintenance(motor_sensors, equipment_type="motor")

        # Pump monitoring with custom thresholds
        graph = predictive_maintenance(pump_sensors, equipment_type="pump",
                                    failure_threshold=0.7, anomaly_sensitivity=0.8)
    """
    valid_equipment = ["motor", "pump", "bearing", "conveyor", "compressor", "generic"]
    if equipment_type not in valid_equipment:
        raise IndustrialError(f"Equipment type must be one of {valid_equipment}, got {equipment_type}")

    if not isinstance(failure_threshold, (int, float)) or not (0.0 <= failure_threshold <= 1.0):
        raise IndustrialError(f"Failure threshold must be between 0.0 and 1.0, got {failure_threshold}")

    if not isinstance(anomaly_sensitivity, (int, float)) or not (0.0 <= anomaly_sensitivity <= 1.0):
        raise IndustrialError(f"Anomaly sensitivity must be between 0.0 and 1.0, got {anomaly_sensitivity}")

    # Create EIR graph for predictive maintenance
    g = EIRGraph()

    # Equipment-specific anomaly patterns
    equipment_patterns = {
        "motor": ["vibration", "current", "temperature"],
        "pump": ["pressure", "flow", "vibration"],
        "bearing": ["vibration", "temperature", "speed"],
        "conveyor": ["speed", "load", "vibration"],
        "compressor": ["pressure", "temperature", "current"],
        "generic": ["sensor_a", "sensor_b", "sensor_c"]
    }

    patterns = equipment_patterns.get(equipment_type, equipment_patterns["generic"])

    # Create anomaly detection neurons for each pattern
    for pattern in patterns:
        # LIF neuron for anomaly detection with adaptive threshold
        anomaly_detector = LIFNeuron(
            f"anomaly_{pattern}",
            v_th=float(anomaly_sensitivity),
            tau_m="10 ms",
        ).as_op()
        g.add_node(f"anomaly_{pattern}", anomaly_detector)

    # Health assessment using temporal integration
    health_monitor = EventFuse("health_assessment", window=health_window,
                              min_count=int(failure_threshold * 50)).as_op()
    g.add_node("health_assessment", health_monitor)

    # Failure prediction based on combined anomaly signals
    failure_predictor = EventFuse("failure_prediction", window=health_window,
                                 min_count=int(failure_threshold * 100)).as_op()
    g.add_node("failure_prediction", failure_predictor)

    # Connect anomaly detectors to health assessment
    for pattern in patterns:
        g.connect(f"anomaly_{pattern}", "spike", "health_assessment", "in")

    # Connect health assessment to failure prediction
    g.connect("health_assessment", "out", "failure_prediction", "in")

    return g
