from __future__ import annotations
from typing import Optional, Dict, Any, List
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine
import json
from ..errors import SecuritySurveillanceError

# Optional Rust acceleration for security surveillance processing
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore


def security_automation(
    source: Any,
    alert_threshold: float = 0.8,
    response_window: str = "2 s",
    coordination_channels: int = 4,
    escalation_levels: Optional[List[str]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Security automation using neuromorphic alert generation and response coordination.

    This algorithm processes threat assessment events to generate alerts and coordinate
    automated security responses. Implements energy-efficient event-driven automation
    for real-time security incident management.

    Args:
        source: Input event source (threat assessment events)
        alert_threshold: Threshold for alert generation (0.0-1.0)
        response_window: Temporal window for response coordination
        coordination_channels: Number of parallel response coordination channels
        escalation_levels: Optional list of escalation levels ["low", "medium", "high", "critical"]
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured security automation graph

    Raises:
        SecuritySurveillanceError: If parameters are invalid or configuration fails

    Example:
        # Basic security automation with default settings
        graph = security_automation(threat_events, alert_threshold=0.9)

        # Multi-channel response coordination
        graph = security_automation(events, coordination_channels=8,
                                  response_window="5 s")

        # Escalation-based automation
        graph = security_automation(events, escalation_levels=["warning", "alert", "emergency"])
    """
    if not isinstance(alert_threshold, (int, float)) or not (0.0 <= alert_threshold <= 1.0):
        raise SecuritySurveillanceError(f"Alert threshold must be between 0.0 and 1.0, got {alert_threshold}")

    if coordination_channels <= 0 or coordination_channels > 16:
        raise SecuritySurveillanceError(f"Coordination channels must be 1-16, got {coordination_channels}")

    # Create EIR graph for security automation
    g = EIRGraph()

    # Alert generation and prioritization
    alert_generate = EventFuse("alert_generate", window="500 ms", min_count=int(alert_threshold * 10)).as_op()
    g.add_node("alert_generate", alert_generate)

    # Response coordination across multiple channels
    for i in range(coordination_channels):
        # Response coordinator for each channel
        response_coord = EventFuse(f"response_{i}", window=response_window, min_count=1).as_op()
        g.add_node(f"response_{i}", response_coord)

        # Response delay for timing coordination
        response_delay = DelayLine(f"delay_{i}", delay=f"{50 * (i + 1)} ms").as_op()
        g.add_node(f"delay_{i}", response_delay)

        # Connect alert generation to response coordination
        g.connect("alert_generate", "out", f"response_{i}", "a")

        # Connect delayed response to coordination
        g.connect(f"delay_{i}", "out", f"response_{i}", "b")

    # Escalation management
    escalation_manage = EventFuse("escalation_manage", window="1 s", min_count=coordination_channels // 2).as_op()
    g.add_node("escalation_manage", escalation_manage)

    # Automated response execution
    response_execute = EventFuse("response_execute", window="200 ms", min_count=1).as_op()
    g.add_node("response_execute", response_execute)

    # Connect response coordinators to escalation management
    for i in range(coordination_channels):
        g.connect(f"response_{i}", "out", "escalation_manage", "a")

    # Connect escalation to execution
    g.connect("escalation_manage", "out", "response_execute", "a")

    # Feedback loop for sustained response
    response_feedback = DelayLine("response_feedback", delay="3 s").as_op()
    g.add_node("response_feedback", response_feedback)

    # Feedback from execution to alert generation for sustained monitoring
    g.connect("response_execute", "out", "response_feedback", "in")
    g.connect("response_feedback", "out", "alert_generate", "a")

    return g