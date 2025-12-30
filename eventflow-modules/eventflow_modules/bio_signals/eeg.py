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

def eeg_processing(
    source: Any,
    sampling_rate: float = 256.0,
    frequency_bands: Dict[str, tuple] = None,
    sleep_staging_window: str = "30 s",
    artifact_threshold: float = 0.8,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    EEG (electroencephalogram) processing for brain wave analysis and sleep staging.

    This algorithm processes EEG signals to extract frequency bands (delta, theta, alpha,
    beta, gamma), perform spectral analysis for sleep staging, and detect artifacts using
    event-based filtering and temporal correlation.

    Args:
        source: Input event source (EEG electrode data)
        sampling_rate: EEG sampling rate in Hz (default 256 Hz for research grade)
        frequency_bands: Custom frequency bands as {'name': (low, high)} in Hz
        sleep_staging_window: Temporal window for sleep stage classification
        artifact_threshold: Threshold for detecting EEG artifacts (0.0-1.0)
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured EEG processing graph

    Raises:
        BioSignalError: If parameters are invalid or electrode configuration fails

    Example:
        # Standard EEG analysis for sleep monitoring
        graph = eeg_processing(eeg_electrodes, sampling_rate=512.0)

        # Custom frequency bands for research
        bands = {'delta': (0.5, 4), 'theta': (4, 8), 'alpha': (8, 12)}
        graph = eeg_processing(sensor, frequency_bands=bands)
    """
    if frequency_bands is None:
        frequency_bands = {
            'delta': (0.5, 4),    # Deep sleep
            'theta': (4, 8),      # Light sleep
            'alpha': (8, 12),     # Relaxed wakefulness
            'beta': (12, 30),     # Active thinking
            'gamma': (30, 100)    # High cognitive processing
        }

    if not isinstance(sampling_rate, (int, float)) or sampling_rate <= 0:
        raise BioSignalError(f"Sampling rate must be positive, got {sampling_rate}")

    if not isinstance(artifact_threshold, (int, float)) or not (0.0 <= artifact_threshold <= 1.0):
        raise BioSignalError(f"Artifact threshold must be between 0.0 and 1.0, got {artifact_threshold}")

    # Validate frequency bands
    for band, (low, high) in frequency_bands.items():
        if low >= high or low < 0 or high > sampling_rate / 2:
            raise BioSignalError(f"Invalid frequency band '{band}': ({low}, {high}) Hz")

    # Create EIR graph for EEG processing
    g = EIRGraph()

    # EEG electrode mapping - assume 8-channel EEG (Fp1, Fp2, C3, C4, P3, P4, O1, O2)
    eeg_channels = XYToChannel("eeg", width=8, height=1).as_op()
    g.add_node("eeg", eeg_channels)

    # Artifact detection - high amplitude events that contaminate EEG
    artifact_detector = EventFuse("artifacts", window="1 s", min_count=int(artifact_threshold * sampling_rate)).as_op()
    g.add_node("artifacts", artifact_detector)

    # Frequency band analysis using event-based filtering
    for band_name, (low_freq, high_freq) in frequency_bands.items():
        # Create band-specific detector
        band_detector = EventFuse(f"{band_name}_band", window="2 s", min_count=int(low_freq * 2)).as_op()
        g.add_node(f"{band_name}_band", band_detector)

        # Connect to electrode input
        g.connect("eeg", "ch", f"{band_name}_band", "in")

    # Sleep staging - temporal correlation of frequency bands
    sleep_stager = EventFuse("sleep_stage", window=sleep_staging_window, min_count=10).as_op()
    g.add_node("sleep_stage", sleep_stager)

    # Connect dominant frequency bands to sleep staging
    # Delta and theta are key for sleep stages
    g.connect("delta_band", "out", "sleep_stage", "in")
    g.connect("theta_band", "out", "sleep_stage", "in")

    # Artifact rejection - suppress outputs when artifacts detected
    g.connect("artifacts", "out", "sleep_stage", "reset")  # Reset on artifacts

    return g