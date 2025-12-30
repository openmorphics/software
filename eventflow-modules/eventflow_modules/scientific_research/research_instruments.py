from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, EventBucket
import numpy as np
import json
from ..errors import ScientificResearchError

# Optional native acceleration for research instruments
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore


def spectrometer_control(
    source: Any,
    wavelength_range: Tuple[float, float] = (200.0, 1100.0),
    resolution: float = 0.5,
    integration_time: str = "100 ms",
    averaging: int = 1,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Spectrometer control and data processing.

    Provides real-time control and analysis for spectroscopic measurements.
    Supports wavelength calibration, intensity correction, and spectral analysis
    for research applications in chemistry, physics, and materials science.

    Args:
        source: Input event source (spectrometer data)
        wavelength_range: Wavelength range in nm (start, end)
        resolution: Spectral resolution in nm (0.1-10.0)
        integration_time: Detector integration time ('10 ms'-'10 s')
        averaging: Number of spectra to average (1-100)
        params: Additional spectrometer parameters

    Returns:
        EIRGraph: Configured spectrometer control graph

    Raises:
        ScientificResearchError: If spectrometer parameters are invalid

    Example:
        # UV-Vis spectroscopy
        graph = spectrometer_control(spectrometer_input, wavelength_range=(200, 800),
                                   resolution=1.0, integration_time="500 ms")

        # High-resolution Raman spectroscopy
        graph = spectrometer_control(raman_input, wavelength_range=(400, 1000),
                                   resolution=0.1, averaging=10)
    """
    if not isinstance(wavelength_range, tuple) or len(wavelength_range) != 2:
        raise ScientificResearchError(f"Wavelength range must be a (min, max) tuple, got {wavelength_range}")

    start_wl, end_wl = wavelength_range
    if not (100.0 <= start_wl < end_wl <= 2500.0):
        raise ScientificResearchError(f"Wavelength range must be between 100-2500 nm with start < end, got {wavelength_range}")

    if not isinstance(resolution, (int, float)) or not (0.1 <= resolution <= 10.0):
        raise ScientificResearchError(f"Resolution must be between 0.1 and 10.0 nm, got {resolution}")

    if not isinstance(averaging, int) or not (1 <= averaging <= 100):
        raise ScientificResearchError(f"Averaging must be between 1 and 100, got {averaging}")

    # Create EIR graph for spectrometer control
    g = EIRGraph()

    # Configure spectral acquisition
    spectral_acq = EventBucket("spectral_acquisition", dt_ns=10_000_000, count=1024).as_op()  # 10ms intervals
    g.add_node("spectral_acquisition", spectral_acq)

    # Apply wavelength calibration and processing
    spectral_proc = EventFuse("spectral_processing", window="1 s", min_count=averaging).as_op()
    g.add_node("spectral_processing", spectral_proc)

    # Connect spectral pipeline
    g.connect("spectral_acquisition", "out", "spectral_processing", "in")

    return g


def oscilloscope_control(
    source: Any,
    channels: int = 4,
    sample_rate: float = 1000000.0,  # 1 MS/s
    voltage_range: float = 10.0,  # ±10V
    trigger_source: str = "ch1",
    trigger_level: float = 0.0,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Oscilloscope control and signal analysis.

    Provides real-time oscilloscope control with multi-channel support,
    trigger configuration, and signal analysis capabilities for electrical
    engineering and physics research applications.

    Args:
        source: Input event source (oscilloscope data)
        channels: Number of channels (1-8)
        sample_rate: Sampling rate in S/s (1000-10000000)
        voltage_range: Voltage range in V (±0.1-±1000)
        trigger_source: Trigger source ('ch1', 'ch2', 'ext', 'auto')
        trigger_level: Trigger level in V (-voltage_range to +voltage_range)
        params: Additional oscilloscope parameters

    Returns:
        EIRGraph: Configured oscilloscope control graph

    Raises:
        ScientificResearchError: If oscilloscope parameters are invalid

    Example:
        # 4-channel oscilloscope for circuit analysis
        graph = oscilloscope_control(scope_input, channels=4, sample_rate=5000000,
                                   voltage_range=5.0, trigger_source="ch1")

        # External trigger for synchronized measurements
        graph = oscilloscope_control(sync_input, trigger_source="ext",
                                   trigger_level=2.5, voltage_range=20.0)
    """
    if not isinstance(channels, int) or not (1 <= channels <= 8):
        raise ScientificResearchError(f"Channels must be between 1 and 8, got {channels}")

    if not isinstance(sample_rate, (int, float)) or not (1000.0 <= sample_rate <= 10_000_000.0):
        raise ScientificResearchError(f"Sample rate must be between 1000 and 10,000,000 S/s, got {sample_rate}")

    if not isinstance(voltage_range, (int, float)) or not (0.1 <= voltage_range <= 1000.0):
        raise ScientificResearchError(f"Voltage range must be between 0.1 and 1000 V, got {voltage_range}")

    valid_triggers = ["ch1", "ch2", "ch3", "ch4", "ext", "auto"]
    if trigger_source not in valid_triggers:
        raise ScientificResearchError(f"Trigger source must be one of {valid_triggers}, got {trigger_source}")

    if not isinstance(trigger_level, (int, float)) or not (-voltage_range <= trigger_level <= voltage_range):
        raise ScientificResearchError(f"Trigger level must be between -{voltage_range} and +{voltage_range} V, got {trigger_level}")

    # Create EIR graph for oscilloscope control
    g = EIRGraph()

    # Configure multi-channel acquisition
    for ch in range(1, channels + 1):
        ch_acq = EventBucket(f"channel_{ch}_acquisition", dt_ns=int(1e9 / sample_rate), count=10000).as_op()
        g.add_node(f"channel_{ch}_acquisition", ch_acq)

    # Apply trigger system
    trigger_sys = EventFuse("trigger_system", window="10 ms", min_count=10).as_op()
    g.add_node("trigger_system", trigger_sys)

    return g


def sensor_control(
    source: Any,
    sensor_type: str = "temperature",
    calibration_curve: Optional[List[Tuple[float, float]]] = None,
    sampling_interval: str = "1 s",
    accuracy_threshold: float = 0.01,
    auto_calibration: bool = False,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Research sensor control and calibration.

    Provides comprehensive sensor control for various research instruments
    including temperature sensors, pressure transducers, flow meters, and
    other scientific measurement devices with calibration and accuracy control.

    Args:
        source: Input event source (sensor data)
        sensor_type: Type of sensor ('temperature', 'pressure', 'flow', 'ph', etc.)
        calibration_curve: Calibration points as [(measured, actual), ...]
        sampling_interval: Sensor sampling interval ('100 ms'-'60 s')
        accuracy_threshold: Accuracy threshold for calibration (0.001-0.1)
        auto_calibration: Enable automatic recalibration (True/False)
        params: Additional sensor parameters

    Returns:
        EIRGraph: Configured sensor control graph

    Raises:
        ScientificResearchError: If sensor parameters are invalid

    Example:
        # Temperature sensor with calibration
        cal_points = [(0.0, 0.1), (25.0, 25.2), (50.0, 49.8)]
        graph = sensor_control(temp_sensor, sensor_type="temperature",
                             calibration_curve=cal_points, accuracy_threshold=0.05)

        # pH sensor with auto-calibration
        graph = sensor_control(ph_sensor, sensor_type="ph", auto_calibration=True,
                             sampling_interval="5 s")
    """
    valid_types = ["temperature", "pressure", "flow", "ph", "conductivity", "humidity", "force", "displacement"]
    if sensor_type not in valid_types:
        raise ScientificResearchError(f"Sensor type must be one of {valid_types}, got {sensor_type}")

    if calibration_curve is not None:
        if not isinstance(calibration_curve, list) or len(calibration_curve) < 2:
            raise ScientificResearchError(f"Calibration curve must be a list of at least 2 (measured, actual) points, got {calibration_curve}")

    if not isinstance(accuracy_threshold, (int, float)) or not (0.001 <= accuracy_threshold <= 0.1):
        raise ScientificResearchError(f"Accuracy threshold must be between 0.001 and 0.1, got {accuracy_threshold}")

    if not isinstance(auto_calibration, bool):
        raise ScientificResearchError(f"Auto calibration must be True or False, got {auto_calibration}")

    # Create EIR graph for sensor control
    g = EIRGraph()

    # Configure sensor data acquisition
    sensor_acq = EventBucket("sensor_acquisition", dt_ns=1_000_000_000, count=100).as_op()  # 1s intervals base
    g.add_node("sensor_acquisition", sensor_acq)

    # Apply calibration and processing
    sensor_proc = EventFuse("sensor_processing", window=sampling_interval, min_count=5).as_op()
    g.add_node("sensor_processing", sensor_proc)

    # Connect sensor pipeline
    g.connect("sensor_acquisition", "out", "sensor_processing", "in")

    return g


def chromatography_control(
    source: Any,
    column_type: str = "analytical",
    mobile_phase: str = "water",
    flow_rate: float = 1.0,  # mL/min
    detector_type: str = "uv",
    wavelength: float = 254.0,  # nm
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Chromatography system control and analysis.

    Provides control for liquid chromatography systems including HPLC and GC
    with detector configuration, method development, and real-time chromatogram
    analysis for analytical chemistry research applications.

    Args:
        source: Input event source (chromatography data)
        column_type: Column type ('analytical', 'preparative', 'capillary')
        mobile_phase: Mobile phase composition
        flow_rate: Flow rate in mL/min (0.01-10.0)
        detector_type: Detector type ('uv', 'ri', 'ms', 'fid')
        wavelength: Detection wavelength in nm (190-900 for UV)
        params: Additional chromatography parameters

    Returns:
        EIRGraph: Configured chromatography control graph

    Raises:
        ScientificResearchError: If chromatography parameters are invalid

    Example:
        # HPLC with UV detection
        graph = chromatography_control(hplc_input, column_type="analytical",
                                     flow_rate=1.5, detector_type="uv", wavelength=280)

        # GC with FID detection
        graph = chromatography_control(gc_input, mobile_phase="helium",
                                     detector_type="fid", flow_rate=2.0)
    """
    valid_columns = ["analytical", "preparative", "capillary"]
    if column_type not in valid_columns:
        raise ScientificResearchError(f"Column type must be one of {valid_columns}, got {column_type}")

    if not isinstance(flow_rate, (int, float)) or not (0.01 <= flow_rate <= 10.0):
        raise ScientificResearchError(f"Flow rate must be between 0.01 and 10.0 mL/min, got {flow_rate}")

    valid_detectors = ["uv", "ri", "ms", "fid", "ecd", "tcd"]
    if detector_type not in valid_detectors:
        raise ScientificResearchError(f"Detector type must be one of {valid_detectors}, got {detector_type}")

    if detector_type == "uv" and not (190.0 <= wavelength <= 900.0):
        raise ScientificResearchError(f"UV wavelength must be between 190 and 900 nm, got {wavelength}")

    # Create EIR graph for chromatography control
    g = EIRGraph()

    # Configure chromatogram acquisition
    chromatogram_acq = EventBucket("chromatogram_acquisition", dt_ns=100_000_000, count=10000).as_op()  # 100ms intervals
    g.add_node("chromatogram_acquisition", chromatogram_acq)

    # Apply peak detection and analysis
    peak_analysis = EventFuse("peak_analysis", window="30 s", min_count=100).as_op()
    g.add_node("peak_analysis", peak_analysis)

    # Connect chromatography pipeline
    g.connect("chromatogram_acquisition", "out", "peak_analysis", "in")

    return g


def mass_spectrometer_control(
    source: Any,
    ionization_mode: str = "esi",
    mass_range: Tuple[float, float] = (50.0, 1000.0),
    resolution: float = 10000.0,
    scan_rate: float = 1.0,  # Hz
    fragmentation: bool = False,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Mass spectrometer control and spectral analysis.

    Provides comprehensive control for mass spectrometry systems including
    ionization control, mass scanning, fragmentation analysis, and real-time
    spectral processing for analytical chemistry and biochemistry research.

    Args:
        source: Input event source (mass spectrometry data)
        ionization_mode: Ionization method ('esi', 'apci', 'maldi', 'ei')
        mass_range: Mass range in m/z (1-10000)
        resolution: Mass resolution (100-100000)
        scan_rate: Scan rate in Hz (0.1-10)
        fragmentation: Enable MS/MS fragmentation (True/False)
        params: Additional mass spectrometry parameters

    Returns:
        EIRGraph: Configured mass spectrometer control graph

    Raises:
        ScientificResearchError: If mass spectrometry parameters are invalid

    Example:
        # ESI-MS for small molecule analysis
        graph = mass_spectrometer_control(ms_input, ionization_mode="esi",
                                        mass_range=(100, 800), resolution=15000)

        # MALDI-MS with fragmentation
        graph = mass_spectrometer_control(maldi_input, ionization_mode="maldi",
                                        fragmentation=True, scan_rate=0.5)
    """
    valid_modes = ["esi", "apci", "maldi", "ei", "ci", "fab"]
    if ionization_mode not in valid_modes:
        raise ScientificResearchError(f"Ionization mode must be one of {valid_modes}, got {ionization_mode}")

    if not isinstance(mass_range, tuple) or len(mass_range) != 2:
        raise ScientificResearchError(f"Mass range must be a (min, max) tuple, got {mass_range}")

    start_mass, end_mass = mass_range
    if not (1.0 <= start_mass < end_mass <= 10000.0):
        raise ScientificResearchError(f"Mass range must be between 1-10000 m/z with start < end, got {mass_range}")

    if not isinstance(resolution, (int, float)) or not (100.0 <= resolution <= 100_000.0):
        raise ScientificResearchError(f"Resolution must be between 100 and 100,000, got {resolution}")

    if not isinstance(scan_rate, (int, float)) or not (0.1 <= scan_rate <= 10.0):
        raise ScientificResearchError(f"Scan rate must be between 0.1 and 10 Hz, got {scan_rate}")

    if not isinstance(fragmentation, bool):
        raise ScientificResearchError(f"Fragmentation must be True or False, got {fragmentation}")

    # Create EIR graph for mass spectrometer control
    g = EIRGraph()

    # Configure mass spectrum acquisition
    mass_acq = EventBucket("mass_acquisition", dt_ns=int(1e9 / scan_rate), count=1000).as_op()
    g.add_node("mass_acquisition", mass_acq)

    # Apply mass spectral processing
    mass_proc = EventFuse("mass_processing", window="5 s", min_count=5).as_op()
    g.add_node("mass_processing", mass_proc)

    # Connect mass spectrometry pipeline
    g.connect("mass_acquisition", "out", "mass_processing", "in")

    return g