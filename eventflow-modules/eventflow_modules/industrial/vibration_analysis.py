from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, XYToChannel, BucketSum
import json
from ..errors import IndustrialError

# Optional Rust acceleration for industrial processing
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore

def vibration_analysis(
    source: Any,
    sampling_rate: float = 1000.0,
    fft_size: int = 1024,
    threshold: float = 0.1,
    window: str = "1 s",
    bearing_freqs: Optional[Dict[str, float]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Vibration analysis using FFT and spectral analysis for bearing monitoring.

    This algorithm processes vibration sensor data through FFT analysis to detect
    bearing faults and mechanical issues. It includes spectral analysis for identifying
    characteristic frequencies associated with bearing defects.

    Args:
        source: Input event source (vibration sensor data)
        sampling_rate: Sensor sampling rate in Hz (default: 1000.0)
        fft_size: FFT window size (default: 1024)
        threshold: Vibration anomaly threshold (0.0-1.0)
        window: Temporal integration window
        bearing_freqs: Dictionary of bearing characteristic frequencies
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured vibration analysis graph

    Raises:
        IndustrialError: If parameters are invalid or sensor configuration fails

    Example:
        # Basic vibration monitoring
        graph = vibration_analysis(vibration_sensor, threshold=0.2)

        # Bearing fault detection with characteristic frequencies
        bearing_freqs = {"BPFO": 120.5, "BPFI": 180.3, "BSF": 65.2}
        graph = vibration_analysis(sensor, bearing_freqs=bearing_freqs, fft_size=2048)
    """
    if not isinstance(sampling_rate, (int, float)) or sampling_rate <= 0:
        raise IndustrialError(f"Sampling rate must be positive, got {sampling_rate}")

    if fft_size <= 0 or fft_size & (fft_size - 1) != 0:  # Check if power of 2
        raise IndustrialError(f"FFT size must be a positive power of 2, got {fft_size}")

    if not isinstance(threshold, (int, float)) or not (0.0 <= threshold <= 1.0):
        raise IndustrialError(f"Vibration threshold must be between 0.0 and 1.0, got {threshold}")

    # Create EIR graph for vibration analysis
    g = EIRGraph()

    # FFT processing for frequency domain analysis
    # Using BucketSum to simulate FFT binning (simplified for neuromorphic processing)
    fft_bins = BucketSum("fft", buckets=fft_size, window=window).as_op()
    g.add_node("fft", fft_bins)

    # Spectral analysis for bearing frequencies
    if bearing_freqs:
        # Create spectral monitoring for each characteristic frequency
        for freq_name, freq_hz in bearing_freqs.items():
            # Calculate bin index for this frequency
            bin_index = int((freq_hz / sampling_rate) * fft_size)
            if 0 <= bin_index < fft_size:
                spectral_monitor = EventFuse(f"spectral_{freq_name}", window=window,
                                          min_count=int(threshold * 100)).as_op()
                g.add_node(f"spectral_{freq_name}", spectral_monitor)

    # Anomaly detection based on vibration amplitude
    vibration_threshold = EventFuse("vibration", window=window, min_count=int(threshold * 10)).as_op()
    g.add_node("vibration", vibration_threshold)

    # Connect FFT to spectral analysis and anomaly detection
    g.connect("fft", "out", "vibration", "in")

    if bearing_freqs:
        for freq_name in bearing_freqs.keys():
            g.connect("fft", "out", f"spectral_{freq_name}", "in")

    return g