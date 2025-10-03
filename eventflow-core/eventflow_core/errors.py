"""
Canonical exception types for eventflow-core.

When the native extension is available, these names alias to the native
exception classes exported by eventflow_core._rust._native so users can
always catch eventflow_core.errors.BucketError / FuseError.
"""

from __future__ import annotations

try:
    # Native wrapper; exposes .native and may re-export helpers
    from ._rust import native as _native  # type: ignore
except Exception:
    _native = None  # type: ignore[assignment]


class BucketError(Exception):
    """Invalid arguments to bucket_sum_i64_f32 (e.g., dt_ns <= 0, length mismatch)."""


class FuseError(Exception):
    """Invalid arguments to fuse_coincidence_i64 (e.g., window_ns <= 0)."""


# If native module exports typed exceptions, alias to them to provide a single
# canonical type across Python and Rust implementations.
if _native is not None:
    if hasattr(_native, "BucketError"):
        BucketError = _native.BucketError  # type: ignore[assignment]
    if hasattr(_native, "FuseError"):
        FuseError = _native.FuseError  # type: ignore[assignment]

__all__ = ["BucketError", "FuseError"]