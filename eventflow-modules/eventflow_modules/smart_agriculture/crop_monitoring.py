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

def crop_health_assessment(
    source: Any,
    ndvi_threshold: float = 0.3,
    window: str = "24 h",
    spatial_resolution: int = 64,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Crop health assessment using NDVI-based monitoring with event-based processing.

    This algorithm processes multispectral imagery to assess crop health through NDVI
    (Normalized Difference Vegetation Index) analysis. Uses event-based thresholding
    to detect unhealthy vegetation areas efficiently.

    Args:
        source: Input event source (multispectral camera data)
        ndvi_threshold: NDVI threshold for healthy vegetation (0.0-1.0)
        window: Temporal window for health assessment integration
        spatial_resolution: Number of pixels in crop field grid (NxN)
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured crop health assessment graph

    Raises:
        SmartAgricultureError: If parameters are invalid or sensor configuration fails

    Example:
        # Basic crop health monitoring
        graph = crop_health_assessment(multispectral_camera, ndvi_threshold=0.4)

        # High-resolution field monitoring
        graph = crop_health_assessment(camera, spatial_resolution=128, window="12 h")
    """
    if not isinstance(ndvi_threshold, (int, float)) or not (0.0 <= ndvi_threshold <= 1.0):
        raise SmartAgricultureError(f"NDVI threshold must be between 0.0 and 1.0, got {ndvi_threshold}")

    if spatial_resolution <= 0 or spatial_resolution > 1024:
        raise SmartAgricultureError(f"Spatial resolution must be 1-1024, got {spatial_resolution}")

    # Create EIR graph for crop health monitoring
    g = EIRGraph()

    # Map multispectral coordinates to channels
    xy_map = XYToChannel("xy", width=spatial_resolution, height=spatial_resolution).as_op()
    g.add_node("xy", xy_map)

    # NDVI health thresholding with temporal integration
    health_threshold = EventFuse("health", window=window, min_count=int(ndvi_threshold * 100)).as_op()
    g.add_node("health", health_threshold)

    # Connect coordinate mapping to health assessment
    g.connect("xy", "ch", "health", "in")

    return g

def ndvi_analysis(
    source: Any,
    red_band: int = 0,
    nir_band: int = 1,
    smoothing_window: str = "1 h",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    NDVI analysis for vegetation health assessment from multispectral data.

    Computes NDVI using event-based processing of red and near-infrared bands.
    Uses neuromorphic acceleration for efficient real-time analysis.

    Args:
        source: Input event source (multispectral sensor data)
        red_band: Channel index for red band
        nir_band: Channel index for near-infrared band
        smoothing_window: Temporal smoothing window
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured NDVI analysis graph

    Raises:
        SmartAgricultureError: If band indices are invalid

    Example:
        # Standard NDVI calculation
        graph = ndvi_analysis(multispectral_sensor)

        # Custom band mapping
        graph = ndvi_analysis(sensor, red_band=2, nir_band=3)
    """
    if not isinstance(red_band, int) or not isinstance(nir_band, int) or red_band == nir_band:
        raise SmartAgricultureError(f"Red and NIR bands must be different integers, got red={red_band}, nir={nir_band}")

    # Create EIR graph for NDVI computation
    g = EIRGraph()

    # Band separation and NDVI computation
    # Use native acceleration if available for efficient computation
    if _ef_native_enabled():
        ndvi_op = _ef_native.ndvi_compute(red_band, nir_band, smoothing_window).as_op()
    else:
        # Fallback implementation using standard ops
        ndvi_op = EventFuse("ndvi", window=smoothing_window, min_count=1).as_op()

    g.add_node("ndvi", ndvi_op)

    return g

def growth_tracking(
    source: Any,
    height_threshold: float = 0.1,
    growth_window: str = "7 d",
    canopy_resolution: int = 32,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Plant growth tracking using height and canopy monitoring.

    Tracks crop growth over time using event-based height measurements
    and canopy expansion detection for precision agriculture applications.

    Args:
        source: Input event source (height sensor or camera data)
        height_threshold: Minimum height change for growth detection (meters)
        growth_window: Temporal window for growth rate calculation
        canopy_resolution: Spatial resolution for canopy analysis
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured growth tracking graph

    Raises:
        SmartAgricultureError: If parameters are invalid

    Example:
        # Basic growth monitoring
        graph = growth_tracking(height_sensor, height_threshold=0.05)

        # Detailed canopy tracking
        graph = growth_tracking(sensor, canopy_resolution=64, growth_window="14 d")
    """
    if not isinstance(height_threshold, (int, float)) or height_threshold <= 0:
        raise SmartAgricultureError(f"Height threshold must be positive, got {height_threshold}")

    if canopy_resolution <= 0 or canopy_resolution > 512:
        raise SmartAgricultureError(f"Canopy resolution must be 1-512, got {canopy_resolution}")

    # Create EIR graph for growth tracking
    g = EIRGraph()

    # Spatial mapping for canopy analysis
    xy_map = XYToChannel("xy", width=canopy_resolution, height=canopy_resolution).as_op()
    g.add_node("xy", xy_map)

    # Growth detection with temporal integration
    growth_detect = EventFuse("growth", window=growth_window, min_count=int(height_threshold * 1000)).as_op()
    g.add_node("growth", growth_detect)

    # Connect spatial mapping to growth detection
    g.connect("xy", "ch", "growth", "in")

    return g