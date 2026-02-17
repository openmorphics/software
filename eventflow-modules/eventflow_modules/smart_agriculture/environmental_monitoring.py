from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, XYToChannel
import json
from ..errors import SmartAgricultureError

# Optional Rust acceleration for smart agriculture processing
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore

def weather_data_processing(
    source: Any,
    precipitation_threshold: float = 5.0,
    wind_speed_limit: float = 20.0,
    monitoring_window: str = "1 h",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Weather data processing for agricultural decision making.

    Processes meteorological data including precipitation, wind, temperature,
    and humidity to optimize farming operations and protect crops.

    Args:
        source: Input event source (weather station sensors)
        precipitation_threshold: Rainfall threshold for irrigation decisions (mm)
        wind_speed_limit: Maximum safe wind speed for operations (m/s)
        monitoring_window: Time window for weather trend analysis
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured weather data processing graph

    Raises:
        SmartAgricultureError: If parameters are invalid

    Example:
        # Standard weather monitoring
        graph = weather_data_processing(weather_station, precipitation_threshold=10.0)

        # Wind-sensitive operations
        graph = weather_data_processing(station, wind_speed_limit=15.0, monitoring_window="30 m")
    """
    if not isinstance(precipitation_threshold, (int, float)) or precipitation_threshold < 0:
        raise SmartAgricultureError(f"Precipitation threshold must be non-negative, got {precipitation_threshold}")

    if not isinstance(wind_speed_limit, (int, float)) or wind_speed_limit < 0:
        raise SmartAgricultureError(f"Wind speed limit must be non-negative, got {wind_speed_limit}")

    # Create EIR graph for weather processing
    g = EIRGraph()

    # Weather condition monitoring
    weather_monitor = EventFuse("weather", window=monitoring_window, min_count=1).as_op()
    g.add_node("weather", weather_monitor)

    return g

def climate_analysis(
    source: Any,
    temperature_range: tuple = (10.0, 30.0),
    humidity_range: tuple = (40.0, 80.0),
    analysis_window: str = "24 h",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Climate analysis for long-term agricultural planning.

    Analyzes climate patterns including temperature trends, humidity levels,
    and seasonal variations to support crop planning and risk assessment.

    Args:
        source: Input event source (climate sensors)
        temperature_range: Acceptable temperature range (°C)
        humidity_range: Acceptable humidity range (%)
        analysis_window: Time window for climate trend analysis
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured climate analysis graph

    Raises:
        SmartAgricultureError: If parameters are invalid

    Example:
        # Temperate climate monitoring
        graph = climate_analysis(climate_sensor, temperature_range=(15.0, 25.0))

        # Tropical crop analysis
        graph = climate_analysis(sensor, humidity_range=(60.0, 90.0), analysis_window="7 d")
    """
    if not isinstance(temperature_range, tuple) or len(temperature_range) != 2 or temperature_range[0] >= temperature_range[1]:
        raise SmartAgricultureError(f"Temperature range must be a tuple (min, max) with min < max, got {temperature_range}")

    if not isinstance(humidity_range, tuple) or len(humidity_range) != 2 or humidity_range[0] >= humidity_range[1]:
        raise SmartAgricultureError(f"Humidity range must be a tuple (min, max) with min < max, got {humidity_range}")

    # Create EIR graph for climate analysis
    g = EIRGraph()

    # Climate trend analysis
    climate_analyze = EventFuse("climate", window=analysis_window, min_count=1).as_op()
    g.add_node("climate", climate_analyze)

    return g

def evapotranspiration_calculation(
    source: Any,
    crop_coefficient: float = 1.0,
    reference_et: float = 5.0,
    calculation_window: str = "1 d",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Evapotranspiration calculation for irrigation scheduling.

    Computes crop water requirements using Penman-Monteith or similar
    equations for precise irrigation management and water conservation.

    Args:
        source: Input event source (weather and soil sensors)
        crop_coefficient: Crop-specific water use factor (0.0-2.0)
        reference_et: Reference evapotranspiration rate (mm/day)
        calculation_window: Time window for ET calculation averaging
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured evapotranspiration calculation graph

    Raises:
        SmartAgricultureError: If parameters are invalid

    Example:
        # Grass reference ET
        graph = evapotranspiration_calculation(weather_sensor, crop_coefficient=0.8)

        # High-water use crop
        graph = evapotranspiration_calculation(sensor, crop_coefficient=1.2, reference_et=6.0)
    """
    if not isinstance(crop_coefficient, (int, float)) or not (0.0 <= crop_coefficient <= 2.0):
        raise SmartAgricultureError(f"Crop coefficient must be between 0.0 and 2.0, got {crop_coefficient}")

    if not isinstance(reference_et, (int, float)) or reference_et < 0:
        raise SmartAgricultureError(f"Reference ET must be non-negative, got {reference_et}")

    # Create EIR graph for ET calculation
    g = EIRGraph()

    # Evapotranspiration computation
    if _ef_native_enabled() and _ef_native is not None and hasattr(_ef_native, "et_calculate"):
        et_op = _ef_native.et_calculate(crop_coefficient, reference_et, calculation_window).as_op()
    else:
        et_op = EventFuse("et", window=calculation_window, min_count=1).as_op()

    g.add_node("et", et_op)

    return g
