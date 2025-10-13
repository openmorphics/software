from __future__ import annotations
import importlib
import os
import warnings
from typing import Optional

_NATIVE_MODULE_NAME = "eventflow_modules._rust._vision_native"


def _env_toggle() -> Optional[bool]:
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
        "EF_NATIVE=1 set but eventflow-modules native extension failed to import; "
        "falling back to pure-Python implementation.",
        RuntimeWarning,
        stacklevel=2,
    )


def is_enabled() -> bool:
    env = _env_toggle()
    if env is True:
        return _native is not None
    if env is False:
        return False
    return _native is not None


# Export the native module under a stable name
native = _native

# Re-export set_log_sink if provided by native
if _native is not None and hasattr(_native, "set_log_sink"):
    set_log_sink = _native.set_log_sink  # type: ignore[attr-defined]

__all__ = ["is_enabled", "native"]
if _native is not None and hasattr(_native, "set_log_sink"):
    __all__.append("set_log_sink")