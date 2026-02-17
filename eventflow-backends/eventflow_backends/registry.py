"""
EventFlow backend registry with package-local built-ins (cpu-sim, gpu-sim).
"""

from __future__ import annotations

import json
import logging
from importlib.resources import files
from typing import Any, Dict, List, Optional

from eventflow_core.validators import validate_eir, validate_event_tensor_jsonl_path

from .cpu_sim.executor import plan_cpu_sim, run_cpu_sim
from .gpu_sim.executor import plan_gpu_sim, run_gpu_sim

_log = logging.getLogger(__name__)


def _load_dcd(package: str) -> Dict[str, Any]:
    path = files(package).joinpath("dcd.json")
    return json.loads(path.read_text(encoding="utf-8"))


class CpuSimBackend:
    def __init__(self) -> None:
        self._dcd: Dict[str, Any] = _load_dcd("eventflow_backends.cpu_sim")

    def name(self) -> str:
        return "cpu-sim"

    def dcd(self) -> Dict[str, Any]:
        return dict(self._dcd)

    def plan(self, eir: Dict[str, Any]) -> Dict[str, Any]:
        issues = validate_eir(eir)
        if issues:
            raise ValueError("EIR validation failed: " + "; ".join(str(i) for i in issues))
        return plan_cpu_sim(eir, self._dcd)

    def run(
        self,
        eir: Dict[str, Any],
        inputs: List[str],
        out_trace_path: str,
        plan: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if plan is None:
            plan = self.plan(eir)
        for path in inputs:
            issues = validate_event_tensor_jsonl_path(path)
            if issues:
                raise ValueError(f"input validation failed for {path}: " + "; ".join(str(i) for i in issues))
        return run_cpu_sim(plan, inputs, out_trace_path)


class GpuSimBackend:
    def __init__(self) -> None:
        self._dcd: Dict[str, Any] = _load_dcd("eventflow_backends.gpu_sim")

    def name(self) -> str:
        return "gpu-sim"

    def dcd(self) -> Dict[str, Any]:
        return dict(self._dcd)

    def plan(self, eir: Dict[str, Any]) -> Dict[str, Any]:
        issues = validate_eir(eir)
        if issues:
            raise ValueError("EIR validation failed: " + "; ".join(str(i) for i in issues))
        return plan_gpu_sim(eir, self._dcd)

    def run(
        self,
        eir: Dict[str, Any],
        inputs: List[str],
        out_trace_path: str,
        plan: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if plan is None:
            plan = self.plan(eir)
        for path in inputs:
            issues = validate_event_tensor_jsonl_path(path)
            if issues:
                raise ValueError(f"input validation failed for {path}: " + "; ".join(str(i) for i in issues))
        return run_gpu_sim(plan, inputs, out_trace_path)


def list_backends() -> List[str]:
    """
    List available backends:
      - Built-ins: cpu-sim, gpu-sim
      - Vendor plugins discovered via importlib.metadata entry points under group 'eventflow_backends'
        Each entry point name should be the backend id (e.g., 'acme-asic-x1').
        The entry point value should resolve to either:
          * a callable factory returning a backend instance with .plan()/.run(), or
          * an object exposing get_backend(name)->instance, or
          * a module/class providing a Backend() constructor.
    """
    names: List[str] = ["cpu-sim", "gpu-sim"]
    try:
        from importlib.metadata import entry_points
        eps = entry_points()
        # Python 3.10/3.11 compatibility:
        # - 3.11+: EntryPoints has .select(group="...")
        # - older: entry_points() returns dict-like mapping
        if hasattr(eps, "select"):
            eps = eps.select(group="eventflow_backends")  # type: ignore[attr-defined]
        elif isinstance(eps, dict):
            eps = eps.get("eventflow_backends", []) or []
        else:
            eps = []
        ep_names = sorted({
            getattr(ep, "name", None) for ep in (eps or [])
            if getattr(ep, "name", None)
        })
        for n in ep_names:
            if n not in names:
                names.append(n)
    except Exception as e:
        _log.warning(f"entry-point discovery failed: {e}")
    return names


def load_backend(name: str):
    """
    Load a backend by id.
    Resolution order:
      1) Built-ins ('cpu-sim', 'gpu-sim')
      2) Entry points under group 'eventflow_backends' with matching entry point name.
         The resolved object may be:
           - a callable factory -> instance
           - an object exposing get_backend(name)
           - a module/class exposing Backend() constructor
    """
    if name in ("cpu-sim", "cpu_sim"):
        return CpuSimBackend()
    if name in ("gpu-sim", "gpu_sim"):
        return GpuSimBackend()
    # Try entry-point plugins
    try:
        from importlib.metadata import entry_points
        eps = entry_points()
        if hasattr(eps, "select"):
            eps = eps.select(group="eventflow_backends")  # type: ignore[attr-defined]
        elif isinstance(eps, dict):
            eps = eps.get("eventflow_backends", []) or []
        else:
            eps = []
        for ep in (eps or []):
            ep_name = getattr(ep, "name", None)
            if ep_name == name:
                obj = ep.load()
                inst = obj() if callable(obj) else obj
                if hasattr(inst, "plan") and hasattr(inst, "run"):
                    return inst
                if hasattr(inst, "get_backend"):
                    return inst.get_backend(name)
                if hasattr(inst, "Backend"):
                    return inst.Backend()
                raise TypeError(f"entry point '{name}' does not provide a backend instance/factory")
    except Exception as e:
        _log.warning(f"entry-point backend load failed for '{name}': {e}")
    raise ValueError(f"unknown backend '{name}'")


def get_backend(name: str):
    """Compatibility helper over the canonical backend loader."""
    return load_backend(name)
