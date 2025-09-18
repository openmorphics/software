"""
EventFlow Backend Registry v0.1

Provides dynamic loading of backend plugins. Ships a built-in 'cpu-sim' backend.
"""

from __future__ import annotations

import json
import os
import importlib.util
import importlib.machinery
import runpy
import types
from typing import Any, Dict, List, Optional


def _base_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _load_module_from(path: str, name: str):
    try:
        # Attempt 1: Standard spec/loader
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is not None and spec.loader is not None:
            try:
                mod = importlib.util.module_from_spec(spec)  # type: ignore
                spec.loader.exec_module(mod)  # type: ignore
                return mod
            except Exception:
                pass

        # Attempt 2: SourceFileLoader
        try:
            loader = importlib.machinery.SourceFileLoader(name, path)
            code = loader.get_code(name)
            mod = types.ModuleType(name)
            mod.__file__ = path  # type: ignore[attr-defined]
            exec(code, mod.__dict__)
            return mod
        except Exception:
            pass

        # Attempt 3: runpy fallback
        ns = runpy.run_path(path)
        mod = types.ModuleType(name)
        mod.__file__ = path  # type: ignore[attr-defined]
        for k, v in ns.items():
            setattr(mod, k, v)
        return mod
    except Exception as e:
        raise RuntimeError(f"cannot load module {name} from {path}: {e}")


class CpuSimBackend:
    def __init__(self) -> None:
        base = _base_dir()
        dcd_path = os.path.join(base, "cpu_sim", "dcd.json")
        if not os.path.isfile(dcd_path):
            raise FileNotFoundError(f"cpu-sim DCD not found: {dcd_path}")
        with open(dcd_path, "r", encoding="utf-8") as f:
            self._dcd: Dict[str, Any] = json.load(f)

        # Load validators
        vpath = os.path.join(base, "..", "eventflow-core", "validators.py")
        vpath = os.path.abspath(vpath)
        self._validators = _load_module_from(vpath, "eventflow_validators")

        # Load executor (plan+run)
        ex_path = os.path.join(base, "cpu_sim", "executor.py")
        self._exec = _load_module_from(ex_path, "eventflow_cpu_sim_executor")

    def name(self) -> str:
        return "cpu-sim"

    def dcd(self) -> Dict[str, Any]:
        return dict(self._dcd)

    def plan(self, eir: Dict[str, Any]) -> Dict[str, Any]:
        # Validate EIR before planning
        issues = self._validators.validate_eir(eir)
        if issues:
            raise ValueError("EIR validation failed: " + "; ".join(str(i) for i in issues))
        return self._exec.plan_cpu_sim(eir, self._dcd)

    def run(
        self,
        eir: Dict[str, Any],
        inputs: List[str],
        out_trace_path: str,
        plan: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if plan is None:
            plan = self.plan(eir)
        # Validate inputs as JSONL headers quickly (optional)
        for p in inputs:
            issues = self._validators.validate_event_tensor_jsonl_path(p)
            if issues:
                # Not fatal, but informative. Enforce strictness for v0.1.
                raise ValueError(f"input validation failed for {p}: " + "; ".join(str(i) for i in issues))
        return self._exec.run_cpu_sim(plan, inputs, out_trace_path)


class GpuSimBackend:
    def __init__(self) -> None:
        base = _base_dir()
        dcd_path = os.path.join(base, "gpu_sim", "dcd.json")
        if not os.path.isfile(dcd_path):
            raise FileNotFoundError(f"gpu-sim DCD not found: {dcd_path}")
        with open(dcd_path, "r", encoding="utf-8") as f:
            self._dcd: Dict[str, Any] = json.load(f)

        # Load validators
        vpath = os.path.join(base, "..", "eventflow-core", "validators.py")
        vpath = os.path.abspath(vpath)
        self._validators = _load_module_from(vpath, "eventflow_validators")

        # Load executor (plan+run)
        ex_path = os.path.join(base, "gpu_sim", "executor.py")
        self._exec = _load_module_from(ex_path, "eventflow_gpu_sim_executor")

    def name(self) -> str:
        return "gpu-sim"

    def dcd(self) -> Dict[str, Any]:
        return dict(self._dcd)

    def plan(self, eir: Dict[str, Any]) -> Dict[str, Any]:
        issues = self._validators.validate_eir(eir)
        if issues:
            raise ValueError("EIR validation failed: " + "; ".join(str(i) for i in issues))
        return self._exec.plan_gpu_sim(eir, self._dcd)

    def run(
        self,
        eir: Dict[str, Any],
        inputs: List[str],
        out_trace_path: str,
        plan: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if plan is None:
            plan = self.plan(eir)
        for p in inputs:
            issues = self._validators.validate_event_tensor_jsonl_path(p)
            if issues:
                raise ValueError(f"input validation failed for {p}: " + "; ".join(str(i) for i in issues))
        return self._exec.run_gpu_sim(plan, inputs, out_trace_path)


def list_backends() -> List[str]:
    return ["cpu-sim", "gpu-sim"]


def load_backend(name: str):
    if name == "cpu-sim":
        return CpuSimBackend()
    if name == "gpu-sim":
        return GpuSimBackend()
    raise ValueError(f"unknown backend '{name}'")
