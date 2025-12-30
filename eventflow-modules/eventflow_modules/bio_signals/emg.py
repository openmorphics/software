from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, XYToChannel
import json
from ..errors import BioSignalError

# Optional Rust acceleration for bio-signal processing
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore

def emg_processing(
    source: Any,
    sampling_rate: float = 1000.0,
    muscle_groups: int = 4,
    gesture_window: str = "200 ms",
    activation_threshold: float = 0.2,
    fatigue_detection: bool = True,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    EMG (electromyogram) processing for muscle activity detection and gesture recognition.

    This algorithm processes EMG signals to detect muscle activation patterns, recognize
    gestures from surface EMG electrodes, and monitor muscle fatigue using event-based
    onset detection and temporal sequencing.

    Args:
        source: Input event source (EMG electrode data)
        sampling_rate: EMG sampling rate in Hz (default 1000 Hz for high-fidelity)
        muscle_groups: Number of muscle groups being monitored (1-8)
        gesture_window: Temporal window for gesture pattern recognition
        activation_threshold: Threshold for muscle activation detection (0.0-1.0)
        fatigue_detection: Enable muscle fatigue monitoring
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured EMG processing graph

    Raises:
        BioSignalError: If parameters are invalid or electrode configuration fails

    Example:
        # Basic muscle activity monitoring
        graph = emg_processing(emg_electrodes, muscle_groups=2)

        # Gesture recognition for prosthetics
        graph = emg_processing(sensor, gesture_window="100 ms", activation_threshold=0.1)
    """
    if not isinstance(sampling_rate, (int, float)) or sampling_rate <= 0:
        raise BioSignalError(f"Sampling rate must be positive, got {sampling_rate}")

    if not (1 <= muscle_groups <= 8):
        raise BioSignalError(f"Muscle groups must be 1-8, got {muscle_groups}")

    if not isinstance(activation_threshold, (int, float)) or not (0.0 <= activation_threshold <= 1.0):
        raise BioSignalError(f"Activation threshold must be between 0.0 and 1.0, got {activation_threshold}")

    # Create EIR graph for EMG processing
    g = EIRGraph()

    # EMG electrode mapping - assume surface electrodes per muscle group
    emg_channels = XYToChannel("emg", width=muscle_groups, height=1).as_op()
    g.add_node("emg", emg_channels)

    # Muscle activation detection - onset of EMG bursts
    for i in range(muscle_groups):
        activation_detector = EventFuse(f"activation_{i}", window="50 ms", min_count=int(activation_threshold * 50)).as_op()
        g.add_node(f"activation_{i}", activation_detector)
        g.connect("emg", "ch", f"activation_{i}", "in")

    # Gesture recognition - temporal patterns across muscle groups
    gesture_detector = EventFuse("gesture", window=gesture_window, min_count=muscle_groups).as_op()
    g.add_node("gesture", gesture_detector)

    # Connect all muscle activations to gesture detector
    for i in range(muscle_groups):
        g.connect(f"activation_{i}", "out", "gesture", f"in_{i}")

    # Muscle fatigue detection (optional) - based on decreasing activation amplitude
    if fatigue_detection:
        fatigue_monitor = EventFuse("fatigue", window="30 s", min_count=10).as_op()
        g.add_node("fatigue", fatigue_monitor)

        # Monitor overall activation patterns
        g.connect("gesture", "out", "fatigue", "in")

    return g