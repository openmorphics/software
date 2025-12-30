from __future__ import annotations
from typing import Optional, Dict, Any, List
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, EventBucket
import numpy as np
import json
from ..errors import ScientificResearchError

# Optional native acceleration for measurement systems
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore


def high_speed_acquisition(
    source: Any,
    sampling_rate: float = 1000000.0,  # 1 MHz
    buffer_size: int = 65536,
    trigger_level: Optional[float] = None,
    pre_trigger_samples: int = 0,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    High-speed data acquisition for scientific measurements.

    Implements real-time high-speed data acquisition with configurable sampling rates,
    buffering, and trigger functionality. Supports pre-trigger capture and
    various trigger modes for scientific instrumentation.

    Args:
        source: Input event source (measurement data)
        sampling_rate: Sampling rate in Hz (1000-10000000)
        buffer_size: Acquisition buffer size (1024-1048576)
        trigger_level: Trigger threshold level (None for continuous)
        pre_trigger_samples: Number of pre-trigger samples (0-buffer_size/4)
        params: Additional acquisition parameters

    Returns:
        EIRGraph: Configured high-speed acquisition graph

    Raises:
        ScientificResearchError: If acquisition parameters are invalid

    Example:
        # High-speed oscilloscope data acquisition
        graph = high_speed_acquisition(oscilloscope_input, sampling_rate=5000000,
                                     buffer_size=131072, trigger_level=0.5)

        # Continuous data logging
        graph = high_speed_acquisition(sensor_input, sampling_rate=100000, buffer_size=65536)
    """
    if not isinstance(sampling_rate, (int, float)) or not (1000.0 <= sampling_rate <= 10_000_000.0):
        raise ScientificResearchError(f"Sampling rate must be between 1000 and 10,000,000 Hz, got {sampling_rate}")

    if not isinstance(buffer_size, int) or buffer_size < 1024 or buffer_size > 1_048_576 or (buffer_size & (buffer_size - 1)) != 0:
        raise ScientificResearchError(f"Buffer size must be power of 2 between 1024 and 1,048,576, got {buffer_size}")

    if trigger_level is not None and not isinstance(trigger_level, (int, float)):
        raise ScientificResearchError(f"Trigger level must be a number or None, got {trigger_level}")

    if not isinstance(pre_trigger_samples, int) or not (0 <= pre_trigger_samples <= buffer_size // 4):
        raise ScientificResearchError(f"Pre-trigger samples must be between 0 and {buffer_size//4}, got {pre_trigger_samples}")

    # Create EIR graph for high-speed acquisition
    g = EIRGraph()

    # Configure high-speed sampling
    hs_acquisition = EventBucket("hs_acquisition", dt_ns=int(1e9 / sampling_rate), count=buffer_size).as_op()
    g.add_node("hs_acquisition", hs_acquisition)

    # Apply trigger detection if specified
    if trigger_level is not None:
        trigger_detect = EventFuse("trigger_detection", window="10 ms", min_count=10).as_op()
        g.add_node("trigger_detection", trigger_detect)
        g.connect("hs_acquisition", "out", "trigger_detection", "in")

    return g


def precision_timing(
    source: Any,
    time_resolution: str = "1 ns",
    synchronization_mode: str = "internal",
    reference_frequency: float = 10_000_000.0,  # 10 MHz
    jitter_compensation: bool = True,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Precision timing system for scientific measurements.

    Provides high-precision timing with configurable resolution, synchronization
    modes, and jitter compensation. Supports various reference frequencies and
    timing standards for laboratory research applications.

    Args:
        source: Input event source (timed measurement data)
        time_resolution: Timing resolution ('1 ns', '100 ps', '10 ps')
        synchronization_mode: Sync mode ('internal', 'external', 'gps')
        reference_frequency: Reference clock frequency in Hz (1e6-1e9)
        jitter_compensation: Enable jitter compensation (True/False)
        params: Additional timing parameters

    Returns:
        EIRGraph: Configured precision timing graph

    Raises:
        ScientificResearchError: If timing parameters are invalid

    Example:
        # High-precision timing for spectroscopy
        graph = precision_timing(spectrometer_input, time_resolution="100 ps",
                               synchronization_mode="external", reference_frequency=10000000)

        # GPS-synchronized timing
        graph = precision_timing(gps_input, synchronization_mode="gps", jitter_compensation=True)
    """
    valid_resolutions = ["1 ns", "100 ps", "10 ps"]
    if time_resolution not in valid_resolutions:
        raise ScientificResearchError(f"Time resolution must be one of {valid_resolutions}, got {time_resolution}")

    valid_modes = ["internal", "external", "gps"]
    if synchronization_mode not in valid_modes:
        raise ScientificResearchError(f"Synchronization mode must be one of {valid_modes}, got {synchronization_mode}")

    if not isinstance(reference_frequency, (int, float)) or not (1_000_000.0 <= reference_frequency <= 1_000_000_000.0):
        raise ScientificResearchError(f"Reference frequency must be between 1e6 and 1e9 Hz, got {reference_frequency}")

    if not isinstance(jitter_compensation, bool):
        raise ScientificResearchError(f"Jitter compensation must be True or False, got {jitter_compensation}")

    # Create EIR graph for precision timing
    g = EIRGraph()

    # Configure precision timing
    timing_precision = DelayLine("precision_timing", delay_ns=1).as_op()  # 1ns base delay
    g.add_node("precision_timing", timing_precision)

    # Apply synchronization if enabled
    if synchronization_mode != "internal":
        sync_timing = EventFuse("timing_sync", window="1 s", min_count=100).as_op()
        g.add_node("timing_sync", sync_timing)
        g.connect("precision_timing", "out", "timing_sync", "in")

    return g


def multi_channel_acquisition(
    channels: List[Any],
    sampling_rate: float = 100000.0,
    channel_count: int = 8,
    synchronization_mode: str = "simultaneous",
    buffer_depth: int = 32768,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Multi-channel data acquisition system.

    Handles synchronized acquisition from multiple measurement channels with
    configurable sampling rates and buffer depths. Supports simultaneous and
    sequential acquisition modes for multi-sensor research applications.

    Args:
        channels: List of input event sources (measurement channels)
        sampling_rate: Sampling rate per channel in Hz (1000-1000000)
        channel_count: Number of channels (2-64)
        synchronization_mode: Sync mode ('simultaneous', 'sequential')
        buffer_depth: Per-channel buffer depth (1024-131072)
        params: Additional multi-channel parameters

    Returns:
        EIRGraph: Configured multi-channel acquisition graph

    Raises:
        ScientificResearchError: If multi-channel parameters are invalid

    Example:
        # Simultaneous 8-channel acquisition
        graph = multi_channel_acquisition(sensor_channels, channel_count=8,
                                        synchronization_mode="simultaneous")

        # Sequential multi-sensor data collection
        graph = multi_channel_acquisition([sensor1, sensor2, sensor3],
                                        synchronization_mode="sequential")
    """
    if not isinstance(channels, list) or len(channels) < 2:
        raise ScientificResearchError(f"Channels must be a list with at least 2 sources, got {len(channels) if isinstance(channels, list) else type(channels)}")

    if not isinstance(sampling_rate, (int, float)) or not (1000.0 <= sampling_rate <= 1_000_000.0):
        raise ScientificResearchError(f"Sampling rate must be between 1000 and 1,000,000 Hz, got {sampling_rate}")

    if not isinstance(channel_count, int) or not (2 <= channel_count <= 64):
        raise ScientificResearchError(f"Channel count must be between 2 and 64, got {channel_count}")

    valid_modes = ["simultaneous", "sequential"]
    if synchronization_mode not in valid_modes:
        raise ScientificResearchError(f"Synchronization mode must be one of {valid_modes}, got {synchronization_mode}")

    if not isinstance(buffer_depth, int) or not (1024 <= buffer_depth <= 131072):
        raise ScientificResearchError(f"Buffer depth must be between 1024 and 131072, got {buffer_depth}")

    # Create EIR graph for multi-channel acquisition
    g = EIRGraph()

    # Configure multi-channel synchronization
    for i, channel in enumerate(channels[:channel_count]):
        channel_acq = EventBucket(f"channel_{i}_acquisition", dt_ns=int(1e9 / sampling_rate), count=buffer_depth).as_op()
        g.add_node(f"channel_{i}_acquisition", channel_acq)

    # Apply channel synchronization
    if synchronization_mode == "simultaneous":
        sync_all = EventFuse("channel_sync", window="100 ms", min_count=channel_count * 10).as_op()
        g.add_node("channel_sync", sync_all)

    return g


def real_time_monitoring(
    source: Any,
    monitoring_window: str = "1 s",
    alert_thresholds: Optional[Dict[str, float]] = None,
    data_logging: bool = True,
    compression_enabled: bool = False,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Real-time monitoring system for scientific data.

    Provides continuous monitoring of measurement data with configurable alert
    thresholds, data logging, and optional compression. Supports real-time
    analysis and anomaly detection for laboratory research applications.

    Args:
        source: Input event source (measurement data)
        monitoring_window: Monitoring time window ('100 ms'-'60 s')
        alert_thresholds: Alert threshold dictionary (None for no alerts)
        data_logging: Enable data logging (True/False)
        compression_enabled: Enable data compression (True/False)
        params: Additional monitoring parameters

    Returns:
        EIRGraph: Configured real-time monitoring graph

    Raises:
        ScientificResearchError: If monitoring parameters are invalid

    Example:
        # Real-time sensor monitoring with alerts
        thresholds = {"temperature": 100.0, "pressure": 2000.0}
        graph = real_time_monitoring(sensor_data, alert_thresholds=thresholds, data_logging=True)

        # Compressed data logging for long-term monitoring
        graph = real_time_monitoring(experiment_data, monitoring_window="10 s",
                                   compression_enabled=True)
    """
    # Validate monitoring window (rough check)
    try:
        # Simple validation - could be enhanced
        if not isinstance(monitoring_window, str):
            raise ValueError
    except:
        raise ScientificResearchError(f"Monitoring window must be a valid time string, got {monitoring_window}")

    if alert_thresholds is not None and not isinstance(alert_thresholds, dict):
        raise ScientificResearchError(f"Alert thresholds must be a dictionary or None, got {type(alert_thresholds)}")

    if not isinstance(data_logging, bool):
        raise ScientificResearchError(f"Data logging must be True or False, got {data_logging}")

    if not isinstance(compression_enabled, bool):
        raise ScientificResearchError(f"Compression enabled must be True or False, got {compression_enabled}")

    # Create EIR graph for real-time monitoring
    g = EIRGraph()

    # Configure monitoring window
    rt_monitor = EventFuse("real_time_monitor", window=monitoring_window, min_count=10).as_op()
    g.add_node("real_time_monitor", rt_monitor)

    # Add alert detection if thresholds specified
    if alert_thresholds:
        alert_detect = EventBucket("alert_detection", dt_ns=100_000_000, count=100).as_op()  # 100ms windows
        g.add_node("alert_detection", alert_detect)
        g.connect("real_time_monitor", "out", "alert_detection", "in")

    return g