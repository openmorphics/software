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

def quality_control(
    source: Any,
    process_type: str = "assembly",
    defect_threshold: float = 0.05,
    parameter_tolerance: float = 0.1,
    monitoring_window: str = "10 s",
    control_limits: Optional[Dict[str, Dict[str, float]]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Quality control monitoring for manufacturing processes and defect detection.

    This algorithm monitors manufacturing processes in real-time to detect defects,
    parameter deviations, and quality issues using neuromorphic processing for
    adaptive threshold detection and process control.

    Args:
        source: Input event source (process sensor data)
        process_type: Type of manufacturing process ("assembly", "machining", "welding", "packaging")
        defect_threshold: Threshold for defect detection (0.0-1.0)
        parameter_tolerance: Tolerance for parameter control (0.0-1.0)
        monitoring_window: Time window for quality assessment
        control_limits: Statistical control limits for parameters
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured quality control graph

    Raises:
        IndustrialError: If parameters are invalid or process configuration fails

    Example:
        # Assembly line quality monitoring
        graph = quality_control(assembly_sensors, process_type="assembly")

        # Machining process control with custom limits
        limits = {"speed": {"upper": 1500, "lower": 1200}, "force": {"upper": 500, "lower": 300}}
        graph = quality_control(machining_sensors, process_type="machining",
                             control_limits=limits, defect_threshold=0.02)
    """
    valid_processes = ["assembly", "machining", "welding", "packaging", "casting", "generic"]
    if process_type not in valid_processes:
        raise IndustrialError(f"Process type must be one of {valid_processes}, got {process_type}")

    if not isinstance(defect_threshold, (int, float)) or not (0.0 <= defect_threshold <= 1.0):
        raise IndustrialError(f"Defect threshold must be between 0.0 and 1.0, got {defect_threshold}")

    if not isinstance(parameter_tolerance, (int, float)) or not (0.0 <= parameter_tolerance <= 1.0):
        raise IndustrialError(f"Parameter tolerance must be between 0.0 and 1.0, got {parameter_tolerance}")

    # Create EIR graph for quality control
    g = EIRGraph()

    # Process-specific monitoring parameters
    process_params = {
        "assembly": ["position", "force", "torque"],
        "machining": ["speed", "feed", "depth"],
        "welding": ["current", "voltage", "temperature"],
        "packaging": ["weight", "dimension", "pressure"],
        "casting": ["temperature", "flow", "pressure"],
        "generic": ["param_a", "param_b", "param_c"]
    }

    params_to_monitor = process_params.get(process_type, process_params["generic"])

    # Create parameter control neurons for each monitored parameter
    for param in params_to_monitor:
        # LIF neuron for parameter deviation detection
        param_control = LIFNeuron(f"control_{param}",
                                v_th=int(parameter_tolerance * 100),
                                tau=5.0).as_op()
        g.add_node(f"control_{param}", param_control)

    # Defect detection using temporal integration
    defect_detector = EventFuse("defect_detection", window=monitoring_window,
                               min_count=int(defect_threshold * 20)).as_op()
    g.add_node("defect_detection", defect_detector)

    # Process quality assessment
    quality_assessment = EventFuse("quality_assessment", window=monitoring_window,
                                  min_count=int((1.0 - defect_threshold) * 50)).as_op()
    g.add_node("quality_assessment", quality_assessment)

    # Statistical process control (SPC) monitoring
    if control_limits:
        for param, limits in control_limits.items():
            if "upper" in limits and "lower" in limits:
                # Create control limit monitoring
                upper_limit = EventFuse(f"upper_{param}", window=monitoring_window,
                                      min_count=int(limits["upper"])).as_op()
                lower_limit = EventFuse(f"lower_{param}", window=monitoring_window,
                                      min_count=int(limits["lower"])).as_op()
                g.add_node(f"upper_{param}", upper_limit)
                g.add_node(f"lower_{param}", lower_limit)

    # Connect parameter controls to defect detection
    for param in params_to_monitor:
        g.connect(f"control_{param}", "spike", "defect_detection", "in")

    # Connect defect detection to quality assessment
    g.connect("defect_detection", "out", "quality_assessment", "in")

    # Connect control limits if defined
    if control_limits:
        for param in control_limits.keys():
            if f"upper_{param}" in [node.name for node in g.nodes.values()]:
                g.connect(f"upper_{param}", "out", "defect_detection", "in")
            if f"lower_{param}" in [node.name for node in g.nodes.values()]:
                g.connect(f"lower_{param}", "out", "defect_detection", "in")

    return g