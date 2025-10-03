"""
Optional Rust acceleration loader for eventflow-core.

- native: the loaded PyO3 module if available, else None
- is_enabled(): whether native acceleration is active (env + availability)

Environment toggle:
  EF_NATIVE=1  -> force native if available, warn and fallback if missing
  EF_NATIVE=0  -> force pure Python
  unset        -> auto: use native when available
"""
from __future__ import annotations
import importlib
import os
import warnings
from typing import Optional

_NATIVE_MODULE_NAME = "eventflow_core._rust._native"


def _env_toggle() -> Optional[bool]:
    """
    Parse EF_NATIVE environment variable.

    Returns:
        True  -> force enable
        False -> force disable
        None  -> auto
    """
    val = os.getenv("EF_NATIVE")
    if val is None:
        return None
    v = val.strip().lower()
    if v in ("1", "true", "on", "yes", "enable"):
        return True
    if v in ("0", "false", "off", "no", "disable"):
        return False
    return None


def _try_import():
    try:
        return importlib.import_module(_NATIVE_MODULE_NAME)
    except Exception:
        return None


_native = _try_import()
_env = _env_toggle()

if _env is True and _native is None:
    warnings.warn(
        "EF_NATIVE=1 set but eventflow_core native extension failed to import; "
        "falling back to pure-Python implementation.",
        RuntimeWarning,
        stacklevel=2,
    )


def is_enabled() -> bool:
    """
    Determine if native acceleration should be used for eventflow-core.
    """
    env = _env_toggle()
    if env is True:
        return _native is not None
    if env is False:
        return False
    return _native is not None


# Expose the native module (or None) under a stable name
native = _native

# Ensure error classes are available at eventflow_core.errors (aliases when native present)
try:
    import eventflow_core.errors as _errors  # type: ignore
except Exception:
    try:
        from .. import errors as _errors  # type: ignore
    except Exception:
        _errors = None  # type: ignore[assignment]

# Re-export set_log_sink if provided by native
if _native is not None and hasattr(_native, "set_log_sink"):
    set_log_sink = _native.set_log_sink  # type: ignore[attr-defined]

__all__ = ["is_enabled", "native"]
if _native is not None and hasattr(_native, "set_log_sink"):
    __all__.append("set_log_sink")