"""
Backend registry facade.

This top-level module delegates to the dynamic registry implementation to avoid
duplicate hard-coded lists and ensure a single source of truth.
"""
from __future__ import annotations
from typing import List, Any

def list_backends() -> List[str]:
    try:
        from .registry.registry import list_backends as _lb  # type: ignore
        return list(_lb())
    except Exception:
        # Safe fallback if registry cannot be imported
        return ["cpu-sim", "gpu-sim"]

def get_backend(backend_id: str) -> Any:
    """
    Compatibility shim used by eventflow_cli. Prefer using the registry loader in ef CLI.
    """
    # Try delegated in-process registry (preferred)
    try:
        from .eventflow_backends import get_backend as _gb  # type: ignore
        return _gb(backend_id)
    except Exception:
        pass
    # Fallback: construct a minimal cpu-sim backend if requested
    if backend_id in ("cpu-sim", "cpu_sim"):
        try:
            from .eventflow_backends.cpu_sim.backend import CPUSimBackend  # type: ignore
            return CPUSimBackend()
        except Exception as e:
            raise RuntimeError("backend.load_failed: cannot load cpu-sim backend") from e
    raise KeyError(f"Unknown backend {backend_id!r}")
