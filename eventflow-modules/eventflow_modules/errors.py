"""
Canonical exception types for eventflow-modules (vision).

When the native extension is available, VisionError aliases to the native class
exported by eventflow_modules._rust._vision_native so users can always catch
eventflow_modules.errors.VisionError across both Python and Rust implementations.
"""

from __future__ import annotations

try:
    # Loader exposes `.native` when available
    from ._rust import native as _native  # type: ignore
except Exception:
    _native = None  # type: ignore[assignment]


class VisionError(Exception):
    """Vision module domain error (e.g., invalid width/height, window/min_count)."""


class TactileError(Exception):
    """Tactile module domain error (e.g., invalid threshold, spatial resolution)."""


class BioSignalError(Exception):
    """Bio-signals module domain error (e.g., invalid sampling rate, electrode config)."""


class EnvironmentalError(Exception):
    """Environmental module domain error (e.g., invalid sensor range, gas threshold)."""


class IndustrialError(Exception):
    """Industrial module domain error (e.g., invalid vibration threshold, bearing config)."""


class FusionError(Exception):
    """Fusion module domain error (e.g., invalid sensor alignment, fusion algorithm config)."""


class AutonomousError(Exception):
    """Autonomous vehicles module domain error (e.g., invalid LiDAR config, sensor fusion params)."""


class SmartCityError(Exception):
    """Smart cities module domain error (e.g., invalid sensor network config, urban IoT threshold)."""


class ScientificResearchError(Exception):
    """Scientific research module domain error (e.g., invalid instrument config, measurement params)."""


class SmartAgricultureError(Exception):
    """Smart agriculture module domain error (e.g., invalid NDVI threshold, soil sensor config)."""
    """Scientific research module domain error (e.g., invalid signal parameters, instrument config)."""


class SecuritySurveillanceError(Exception):
    """Security/surveillance module domain error (e.g., invalid threshold, sensor config, threat assessment params)."""


# If native module exports the typed exception, alias to it for consistency.
if _native is not None and hasattr(_native, "VisionError"):
    VisionError = _native.VisionError  # type: ignore[assignment]

__all__ = ["VisionError", "TactileError", "BioSignalError", "EnvironmentalError", "IndustrialError", "FusionError", "AutonomousError", "SmartCityError", "ScientificResearchError"]