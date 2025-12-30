"""Tactile/haptic domain module exports. See usage examples in [README](eventflow-modules/README.md:1)."""
from __future__ import annotations
from .pressure_detection import pressure_detection
from .texture_analysis import texture_analysis
__all__ = ["pressure_detection", "texture_analysis"]