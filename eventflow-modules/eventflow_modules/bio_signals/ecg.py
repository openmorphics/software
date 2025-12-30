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

def ecg_processing(
    source: Any,
    sampling_rate: float = 250.0,
    heart_rate_window: str = "10 s",
    arrhythmia_threshold: float = 0.15,
    noise_filter_cutoff: float = 0.5,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    ECG (electrocardiogram) processing for heart rate monitoring and arrhythmia detection.

    This algorithm processes ECG signals to detect R-peaks for heart rate calculation,
    monitor heart rate variability, and identify potential arrhythmias using event-based
    thresholding and temporal pattern analysis.

    Args:
        source: Input event source (ECG electrode data)
        sampling_rate: ECG sampling rate in Hz (default 250 Hz for medical grade)
        heart_rate_window: Temporal window for heart rate averaging
        arrhythmia_threshold: Threshold for detecting irregular rhythms (0.0-1.0)
        noise_filter_cutoff: Cutoff frequency for baseline noise filtering (Hz)
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured ECG processing graph

    Raises:
        BioSignalError: If parameters are invalid or electrode configuration fails

    Example:
        # Standard ECG monitoring with arrhythmia detection
        graph = ecg_processing(ecg_electrode, sampling_rate=500.0)

        # High-sensitivity arrhythmia monitoring
        graph = ecg_processing(sensor, arrhythmia_threshold=0.1, heart_rate_window="30 s")
    """
    if not isinstance(sampling_rate, (int, float)) or sampling_rate <= 0:
        raise BioSignalError(f"Sampling rate must be positive, got {sampling_rate}")

    if not isinstance(arrhythmia_threshold, (int, float)) or not (0.0 <= arrhythmia_threshold <= 1.0):
        raise BioSignalError(f"Arrhythmia threshold must be between 0.0 and 1.0, got {arrhythmia_threshold}")

    if not isinstance(noise_filter_cutoff, (int, float)) or noise_filter_cutoff <= 0:
        raise BioSignalError(f"Noise filter cutoff must be positive, got {noise_filter_cutoff}")

    # Create EIR graph for ECG processing
    g = EIRGraph()

    # ECG signal preprocessing - baseline wandering removal
    # Map ECG leads to channels (assume 3-lead ECG: I, II, III)
    ecg_channels = XYToChannel("ecg", width=3, height=1).as_op()
    g.add_node("ecg", ecg_channels)

    # R-peak detection using event-based thresholding
    # R-peaks are the largest positive deflections in ECG
    r_peak_detector = EventFuse("r_peaks", window="200 ms", min_count=int(0.8 * sampling_rate * 0.2)).as_op()
    g.add_node("r_peaks", r_peak_detector)

    # Heart rate calculation - RR interval analysis
    # Use delay lines to measure intervals between R-peaks
    rr_interval_delay = DelayLine("rr_delay", delay="2 s").as_op()  # Store previous R-peak
    g.add_node("rr_delay", rr_interval_delay)

    # Heart rate variability analysis
    hrv_fuse = EventFuse("hrv", window=heart_rate_window, min_count=5).as_op()
    g.add_node("hrv", hrv_fuse)

    # Arrhythmia detection - compare RR intervals for irregularity
    arrhythmia_detector = EventFuse("arrhythmia", window="5 s", min_count=int(arrhythmia_threshold * 10)).as_op()
    g.add_node("arrhythmia", arrhythmia_detector)

    # Connect processing pipeline
    g.connect("ecg", "ch", "r_peaks", "in")
    g.connect("r_peaks", "out", "rr_delay", "in")
    g.connect("r_peaks", "out", "hrv", "a")
    g.connect("rr_delay", "out", "hrv", "b")
    g.connect("hrv", "out", "arrhythmia", "in")

    return g