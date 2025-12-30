from __future__ import annotations
from typing import Optional, Dict, Any, List
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, LIFNeuron, ExpSynapse
import json
from ..errors import SecuritySurveillanceError

# Optional Rust acceleration for security surveillance processing
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore


def threat_assessment(
    source: Any,
    risk_threshold: float = 0.7,
    behavior_window: str = "5 s",
    analysis_channels: int = 8,
    threat_patterns: Optional[List[str]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Threat assessment using neuromorphic behavior analysis and risk evaluation.

    This algorithm processes security events to assess potential threats by analyzing
    behavioral patterns and evaluating risk levels using spiking neural networks.
    Implements energy-efficient threat classification for real-time security monitoring.

    Args:
        source: Input event source (intrusion detection events, sensor data)
        risk_threshold: Threshold for threat classification (0.0-1.0)
        behavior_window: Temporal window for behavior pattern analysis
        analysis_channels: Number of parallel analysis channels for pattern recognition
        threat_patterns: Optional list of known threat pattern signatures
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured threat assessment graph

    Raises:
        SecuritySurveillanceError: If parameters are invalid or configuration fails

    Example:
        # Basic threat assessment with default settings
        graph = threat_assessment(intrusion_events, risk_threshold=0.8)

        # Multi-channel behavior analysis
        graph = threat_assessment(sensor_data, analysis_channels=16,
                                behavior_window="10 s")

        # Pattern-based threat detection
        graph = threat_assessment(events, threat_patterns=["rapid_motion", "zone_violation"])
    """
    if not isinstance(risk_threshold, (int, float)) or not (0.0 <= risk_threshold <= 1.0):
        raise SecuritySurveillanceError(f"Risk threshold must be between 0.0 and 1.0, got {risk_threshold}")

    if analysis_channels <= 0 or analysis_channels > 64:
        raise SecuritySurveillanceError(f"Analysis channels must be 1-64, got {analysis_channels}")

    # Create EIR graph for threat assessment
    g = EIRGraph()

    # Behavioral pattern analysis using spiking neurons
    for i in range(analysis_channels):
        # LIF neuron for pattern recognition
        pattern_neuron = LIFNeuron(f"pattern_{i}", tau_m="50 ms", v_th=risk_threshold, v_reset=0.0).as_op()
        g.add_node(f"pattern_{i}", pattern_neuron)

        # Synaptic plasticity for learning threat patterns
        synapse = ExpSynapse(f"synapse_{i}", tau_s="100 ms", weight=0.5).as_op()
        g.add_node(f"synapse_{i}", synapse)

        # Temporal integration for behavior analysis
        behavior_integrate = EventFuse(f"behavior_{i}", window=behavior_window, min_count=2).as_op()
        g.add_node(f"behavior_{i}", behavior_integrate)

        # Connect synapse to pattern neuron
        g.connect(f"synapse_{i}", "post", f"pattern_{i}", "in")

        # Connect behavior analysis to synapse
        g.connect(f"behavior_{i}", "out", f"synapse_{i}", "pre")

    # Risk evaluation and classification
    risk_evaluate = EventFuse("risk_evaluate", window="1 s", min_count=int(risk_threshold * analysis_channels)).as_op()
    g.add_node("risk_evaluate", risk_evaluate)

    # Threat classification output
    threat_classify = EventFuse("threat_classify", window="500 ms", min_count=1).as_op()
    g.add_node("threat_classify", threat_classify)

    # Connect pattern neurons to risk evaluation
    for i in range(analysis_channels):
        g.connect(f"pattern_{i}", "spike", "risk_evaluate", "a")

    # Connect risk evaluation to threat classification
    g.connect("risk_evaluate", "out", "threat_classify", "a")

    # Temporal feedback for sustained threat detection
    threat_delay = DelayLine("threat_memory", delay="2 s").as_op()
    g.add_node("threat_memory", threat_delay)

    # Feedback loop for threat persistence
    g.connect("threat_classify", "out", "threat_memory", "in")
    g.connect("threat_memory", "out", "risk_evaluate", "b")

    return g