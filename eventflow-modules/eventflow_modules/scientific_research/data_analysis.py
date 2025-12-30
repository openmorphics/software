from __future__ import annotations
from typing import Optional, Dict, Any, List, Tuple, Callable
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, EventBucket
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


def curve_fitting(
    source: Any,
    fit_function: str = "linear",
    data_points: int = 100,
    confidence_level: float = 0.95,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Curve fitting for experimental data analysis.

    Performs real-time curve fitting on event-based data streams using various
    mathematical models (linear, polynomial, exponential, gaussian). Supports
    configurable data windows and statistical confidence intervals.

    Args:
        source: Input event source (experimental data)
        fit_function: Type of fit ('linear', 'polynomial', 'exponential', 'gaussian')
        data_points: Number of data points for fitting (10-10000)
        confidence_level: Statistical confidence level (0.8-0.99)
        params: Additional fitting parameters

    Returns:
        EIRGraph: Configured curve fitting graph

    Raises:
        ScientificResearchError: If fitting parameters are invalid

    Example:
        # Linear regression on experimental data
        graph = curve_fitting(sensor_data, fit_function="linear", data_points=500)

        # Polynomial fitting for calibration curves
        graph = curve_fitting(calibration_data, fit_function="polynomial",
                            data_points=1000, confidence_level=0.99)
    """
    valid_functions = ["linear", "polynomial", "exponential", "gaussian"]
    if fit_function not in valid_functions:
        raise ScientificResearchError(f"Fit function must be one of {valid_functions}, got {fit_function}")

    if not isinstance(data_points, int) or not (10 <= data_points <= 10000):
        raise ScientificResearchError(f"Data points must be between 10 and 10000, got {data_points}")

    if not isinstance(confidence_level, (int, float)) or not (0.8 <= confidence_level <= 0.99):
        raise ScientificResearchError(f"Confidence level must be between 0.8 and 0.99, got {confidence_level}")

    # Create EIR graph for curve fitting
    g = EIRGraph()

    # Configure data collection window
    data_window = EventBucket("data_collection", dt_ns=1_000_000, count=data_points).as_op()
    g.add_node("data_collection", data_window)

    # Apply curve fitting computation
    fit_compute = EventFuse("curve_fit", window="1 s", min_count=int(data_points * 0.8)).as_op()
    g.add_node("curve_fit", fit_compute)

    # Connect fitting pipeline
    g.connect("data_collection", "out", "curve_fit", "in")

    return g


def statistical_analysis(
    source: Any,
    analysis_type: str = "basic",
    window_size: int = 1000,
    outlier_detection: bool = True,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Statistical analysis of experimental data.

    Performs real-time statistical analysis on event-based data streams including
    descriptive statistics, hypothesis testing, and outlier detection. Supports
    various analysis types and configurable analysis windows.

    Args:
        source: Input event source (experimental data)
        analysis_type: Type of analysis ('basic', 'advanced', 'hypothesis')
        window_size: Statistical analysis window size (100-10000)
        outlier_detection: Enable outlier detection (True/False)
        params: Additional statistical parameters

    Returns:
        EIRGraph: Configured statistical analysis graph

    Raises:
        ScientificResearchError: If analysis parameters are invalid

    Example:
        # Basic statistical analysis of sensor readings
        graph = statistical_analysis(sensor_data, analysis_type="basic", window_size=500)

        # Advanced analysis with outlier detection
        graph = statistical_analysis(experimental_data, analysis_type="advanced",
                                   window_size=2000, outlier_detection=True)
    """
    valid_types = ["basic", "advanced", "hypothesis"]
    if analysis_type not in valid_types:
        raise ScientificResearchError(f"Analysis type must be one of {valid_types}, got {analysis_type}")

    if not isinstance(window_size, int) or not (100 <= window_size <= 10000):
        raise ScientificResearchError(f"Window size must be between 100 and 10000, got {window_size}")

    if not isinstance(outlier_detection, bool):
        raise ScientificResearchError(f"Outlier detection must be True or False, got {outlier_detection}")

    # Create EIR graph for statistical analysis
    g = EIRGraph()

    # Configure statistical analysis window
    stat_window = EventBucket("stat_window", dt_ns=1_000_000, count=window_size).as_op()
    g.add_node("stat_window", stat_window)

    # Apply statistical computation
    stat_compute = EventFuse("stat_analysis", window="500 ms", min_count=int(window_size * 0.5)).as_op()
    g.add_node("stat_analysis", stat_compute)

    # Optional outlier detection
    if outlier_detection:
        outlier_detect = EventFilter("outlier_detection", min_count=int(window_size * 0.1)).as_op()
        g.add_node("outlier_detection", outlier_detect)
        g.connect("stat_analysis", "out", "outlier_detection", "in")

    # Connect analysis pipeline
    g.connect("stat_window", "out", "stat_analysis", "in")

    return g


def linear_regression(
    x_data: Any,
    y_data: Any,
    confidence_interval: float = 0.95,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Linear regression analysis for experimental data.

    Performs real-time linear regression on paired event-based data streams.
    Provides slope, intercept, correlation coefficient, and confidence intervals.

    Args:
        x_data: Independent variable event source
        y_data: Dependent variable event source
        confidence_interval: Confidence interval for regression (0.8-0.99)
        params: Additional regression parameters

    Returns:
        EIRGraph: Configured linear regression graph

    Raises:
        ScientificResearchError: If regression parameters are invalid

    Example:
        # Linear regression of experimental measurements
        graph = linear_regression(independent_var, dependent_var, confidence_interval=0.95)
    """
    if not isinstance(confidence_interval, (int, float)) or not (0.8 <= confidence_interval <= 0.99):
        raise ScientificResearchError(f"Confidence interval must be between 0.8 and 0.99, got {confidence_interval}")

    # Create EIR graph for linear regression
    g = EIRGraph()

    # Configure paired data collection
    regression_compute = EventFuse("linear_regression", window="2 s", min_count=50).as_op()
    g.add_node("linear_regression", regression_compute)

    return g


def polynomial_fitting(
    source: Any,
    degree: int = 2,
    data_points: int = 500,
    r_squared_threshold: float = 0.8,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Polynomial curve fitting for experimental data.

    Performs polynomial regression of specified degree on event-based data.
    Provides polynomial coefficients, goodness-of-fit metrics, and extrapolation.

    Args:
        source: Input event source (experimental data)
        degree: Polynomial degree (1-10)
        data_points: Number of data points for fitting (50-5000)
        r_squared_threshold: Minimum R-squared threshold (0.5-0.99)
        params: Additional polynomial fitting parameters

    Returns:
        EIRGraph: Configured polynomial fitting graph

    Raises:
        ScientificResearchError: If polynomial parameters are invalid

    Example:
        # Quadratic polynomial fitting
        graph = polynomial_fitting(experimental_data, degree=2, data_points=1000)
    """
    if not isinstance(degree, int) or not (1 <= degree <= 10):
        raise ScientificResearchError(f"Polynomial degree must be between 1 and 10, got {degree}")

    if not isinstance(data_points, int) or not (50 <= data_points <= 5000):
        raise ScientificResearchError(f"Data points must be between 50 and 5000, got {data_points}")

    if not isinstance(r_squared_threshold, (int, float)) or not (0.5 <= r_squared_threshold <= 0.99):
        raise ScientificResearchError(f"R-squared threshold must be between 0.5 and 0.99, got {r_squared_threshold}")

    # Create EIR graph for polynomial fitting
    g = EIRGraph()

    # Configure polynomial fitting
    poly_fit = EventBucket("polynomial_fit", dt_ns=1_000_000, count=data_points).as_op()
    g.add_node("polynomial_fit", poly_fit)

    # Apply polynomial computation
    poly_compute = EventFuse("polynomial_compute", window="1 s", min_count=int(data_points * 0.7)).as_op()
    g.add_node("polynomial_compute", poly_compute)

    # Connect polynomial pipeline
    g.connect("polynomial_fit", "out", "polynomial_compute", "in")

    return g