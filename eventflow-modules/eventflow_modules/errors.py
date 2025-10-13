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


# If native module exports the typed exception, alias to it for consistency.
if _native is not None and hasattr(_native, "VisionError"):
    VisionError = _native.VisionError  # type: ignore[assignment]

__all__ = ["VisionError"]