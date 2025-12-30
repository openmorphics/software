"""Scientific research module exports. See usage examples in [README](eventflow-modules/README.md:1)."""
from __future__ import annotations
from .signal_processing import fft_analysis, signal_filtering, correlation_analysis
from .data_analysis import curve_fitting, statistical_analysis
from .measurement_systems import high_speed_acquisition, precision_timing
from .research_instruments import spectrometer_control, oscilloscope_control, sensor_control
__all__ = ["fft_analysis", "signal_filtering", "correlation_analysis",
           "curve_fitting", "statistical_analysis",
           "high_speed_acquisition", "precision_timing",
           "spectrometer_control", "oscilloscope_control", "sensor_control"]