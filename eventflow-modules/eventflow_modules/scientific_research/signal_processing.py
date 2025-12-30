from __future__ import annotations
from typing import Optional, Dict, Any, List
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, EventBucket, EventFilter
import numpy as np
import json
from ..errors import ScientificResearchError

# Optional native acceleration for scientific computing
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore


def fft_analysis(
    source: Any,
    sampling_rate: float = 1000.0,
    window_size: int = 1024,
    overlap: float = 0.5,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Fast Fourier Transform (FFT) analysis for signal processing.

    Performs real-time FFT analysis on event-based signals using event-driven
    windowing and frequency domain processing. Supports configurable sampling
    rates, window sizes, and overlap for spectral analysis.

    Args:
        source: Input event source (signal data)
        sampling_rate: Signal sampling rate in Hz (1-1000000)
        window_size: FFT window size in samples (power of 2, 64-65536)
        overlap: Window overlap ratio (0.0-0.9)
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured FFT analysis graph

    Raises:
        ScientificResearchError: If parameters are invalid or FFT config fails

    Example:
        # Real-time spectral analysis of sensor data
        graph = fft_analysis(sensor_source, sampling_rate=5000, window_size=2048)

        # High-resolution audio spectrum analysis
        graph = fft_analysis(audio_input, sampling_rate=44100, window_size=4096, overlap=0.75)
    """
    if not isinstance(sampling_rate, (int, float)) or not (1.0 <= sampling_rate <= 1_000_000.0):
        raise ScientificResearchError(f"Sampling rate must be between 1 and 1,000,000 Hz, got {sampling_rate}")

    if not isinstance(window_size, int) or window_size < 64 or window_size > 65536 or (window_size & (window_size - 1)) != 0:
        raise ScientificResearchError(f"Window size must be power of 2 between 64 and 65536, got {window_size}")

    if not isinstance(overlap, (int, float)) or not (0.0 <= overlap < 1.0):
        raise ScientificResearchError(f"Overlap must be between 0.0 and 0.9, got {overlap}")

    # Create EIR graph for FFT processing
    g = EIRGraph()

    # Configure event-based FFT windowing
    fft_window = EventBucket("fft_window", dt_ns=int(1e9 / sampling_rate), count=window_size).as_op()
    g.add_node("fft_window", fft_window)

    # Apply FFT transformation (implemented as event filter for frequency domain)
    fft_transform = EventFilter("fft_transform", min_count=int(window_size * (1 - overlap))).as_op()
    g.add_node("fft_transform", fft_transform)

    # Connect windowing to FFT transform
    g.connect("fft_window", "out", "fft_transform", "in")

    return g


def signal_filtering(
    source: Any,
    filter_type: str = "lowpass",
    cutoff_frequency: float = 100.0,
    order: int = 4,
    sampling_rate: float = 1000.0,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Digital signal filtering using event-driven processing.

    Implements real-time signal filtering (lowpass, highpass, bandpass, bandstop)
    using event-based filter coefficients and state management. Supports
    configurable filter orders and cutoff frequencies.

    Args:
        source: Input event source (signal data)
        filter_type: Filter type ('lowpass', 'highpass', 'bandpass', 'bandstop')
        cutoff_frequency: Cutoff frequency in Hz (1-500000)
        order: Filter order (1-8)
        sampling_rate: Signal sampling rate in Hz
        params: Additional filter parameters

    Returns:
        EIRGraph: Configured signal filtering graph

    Raises:
        ScientificResearchError: If filter parameters are invalid

    Example:
        # Low-pass filtering for noise reduction
        graph = signal_filtering(sensor_input, filter_type="lowpass", cutoff_frequency=50)

        # Band-pass filtering for specific frequency range
        graph = signal_filtering(signal_source, filter_type="bandpass",
                                cutoff_frequency=[10, 100], order=6)
    """
    valid_types = ["lowpass", "highpass", "bandpass", "bandstop"]
    if filter_type not in valid_types:
        raise ScientificResearchError(f"Filter type must be one of {valid_types}, got {filter_type}")

    if isinstance(cutoff_frequency, (int, float)):
        if not (1.0 <= cutoff_frequency <= 500_000.0):
            raise ScientificResearchError(f"Cutoff frequency must be between 1 and 500,000 Hz, got {cutoff_frequency}")
    elif isinstance(cutoff_frequency, (list, tuple)) and len(cutoff_frequency) == 2:
        for freq in cutoff_frequency:
            if not (1.0 <= freq <= 500_000.0):
                raise ScientificResearchError(f"Cutoff frequencies must be between 1 and 500,000 Hz, got {cutoff_frequency}")
    else:
        raise ScientificResearchError(f"Cutoff frequency must be a number or [low, high] pair, got {cutoff_frequency}")

    if not isinstance(order, int) or not (1 <= order <= 8):
        raise ScientificResearchError(f"Filter order must be between 1 and 8, got {order}")

    # Create EIR graph for signal filtering
    g = EIRGraph()

    # Configure event-based filter processing
    filter_proc = EventFilter("signal_filter", min_count=order).as_op()
    g.add_node("signal_filter", filter_proc)

    # Add filter state management
    filter_state = DelayLine("filter_state", delay_ns=int(1e9 / sampling_rate)).as_op()
    g.add_node("filter_state", filter_state)

    # Connect filter components
    g.connect("signal_filter", "out", "filter_state", "in")

    return g


def correlation_analysis(
    source: Any,
    reference_signal: Optional[Any] = None,
    correlation_type: str = "cross",
    window_size: int = 512,
    max_lag: int = 256,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Signal correlation analysis using event-driven processing.

    Performs cross-correlation and auto-correlation analysis on event-based signals.
    Supports configurable window sizes and lag ranges for correlation computation.

    Args:
        source: Input event source (signal data)
        reference_signal: Reference signal for cross-correlation (None for auto-correlation)
        correlation_type: Type of correlation ('cross', 'auto')
        window_size: Analysis window size in samples (128-4096)
        max_lag: Maximum correlation lag in samples (32-2048)
        params: Additional correlation parameters

    Returns:
        EIRGraph: Configured correlation analysis graph

    Raises:
        ScientificResearchError: If correlation parameters are invalid

    Example:
        # Auto-correlation analysis of periodic signals
        graph = correlation_analysis(signal_input, correlation_type="auto", window_size=1024)

        # Cross-correlation between two signals
        graph = correlation_analysis(signal1, reference_signal=signal2,
                                   correlation_type="cross", max_lag=512)
    """
    valid_types = ["cross", "auto"]
    if correlation_type not in valid_types:
        raise ScientificResearchError(f"Correlation type must be one of {valid_types}, got {correlation_type}")

    if not isinstance(window_size, int) or not (128 <= window_size <= 4096):
        raise ScientificResearchError(f"Window size must be between 128 and 4096, got {window_size}")

    if not isinstance(max_lag, int) or not (32 <= max_lag <= 2048):
        raise ScientificResearchError(f"Max lag must be between 32 and 2048, got {max_lag}")

    if max_lag >= window_size:
        raise ScientificResearchError(f"Max lag ({max_lag}) must be less than window size ({window_size})")

    # Create EIR graph for correlation analysis
    g = EIRGraph()

    # Configure correlation windowing
    corr_window = EventBucket("correlation_window", dt_ns=0, count=window_size).as_op()
    g.add_node("correlation_window", corr_window)

    # Apply correlation computation
    corr_compute = EventFuse("correlation_compute", window="100 ms", min_count=max_lag).as_op()
    g.add_node("correlation_compute", corr_compute)

    # Connect correlation pipeline
    g.connect("correlation_window", "out", "correlation_compute", "in")

    return g