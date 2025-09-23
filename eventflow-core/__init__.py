from __future__ import annotations

"""
EventFlow Core SDK — Runtime Engine v0.1

Provides:
- version() -> str
- compile_and_run(graph, backend="auto", constraints=None) -> dict

The runtime performs:
- EIR loading and validation
- Backend registry discovery
- Capability-aware planning (delegated to backend)
- Execution to produce a golden trace
- Error handling and optional constraint overrides

This module avoids strict packaging requirements by dynamically loading
internal modules (validators, backend registry) via robust loaders,
mirroring the CLI strategy.
"""

import os
import json
import logging
import types
import runpy
from typing import Optional, Dict, Any, List, Tuple

__all__ = ["version", "compile_and_run"]

# Logger
_log = logging.getLogger("eventflow.core.runtime")
if not _log.handlers:
    h = logging.StreamHandler()
    fmt = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    h.setFormatter(fmt)
    _log.addHandler(h)
    _log.setLevel(logging.INFO)


def version() -> str:
    return "0.1.0"


def _repo_root() -> str:
    # eventflow-core/__init__.py -> repo root
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _load_module_with_fallback(path: str, name: str):
    import importlib.util
    import importlib.machinery
    # Attempt 1: Standard spec/loader
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is not None and spec.loader is not None:
        try:
            mod = importlib.util.module_from_spec(spec)  # type: ignore
            # Register in sys.modules before exec to satisfy typing/dataclasses edge cases
            import sys
            sys.modules[name] = mod
            spec.loader.exec_module(mod)  # type: ignore
            return mod
        except Exception as e:
            _log.warning(f"backend discovery failed: {e}")
    # Attempt 2: SourceFileLoader
    try:
        loader = importlib.machinery.SourceFileLoader(name, path)
        code = loader.get_code(name)
        mod = types.ModuleType(name)
        mod.__file__ = path  # type: ignore[attr-defined]
        exec(code, mod.__dict__)
        return mod
    except Exception as e:
        _log.warning(f"module loader (SourceFileLoader) failed for '{name}': {e}")
    # Attempt 3: runpy fallback
    ns = runpy.run_path(path)
    mod = types.ModuleType(name)
    mod.__file__ = path  # type: ignore[attr-defined]
    for k, v in ns.items():
        setattr(mod, k, v)
    return mod


def _load_validators():
    path = os.path.join(_repo_root(), "eventflow-core", "validators.py")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"validators not found at {path}")
    return _load_module_with_fallback(path, "eventflow_validators_runtime")


def _load_backend_registry():
    path = os.path.join(_repo_root(), "eventflow-backends", "registry", "registry.py")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"backend registry not found at {path}")
    return _load_module_with_fallback(path, "eventflow_backend_registry_runtime")


def _ensure_list(x: Any) -> List[str]:
    if x is None:
        return []
    if isinstance(x, (list, tuple)):
        return [str(i) for i in x]
    return [str(x)]


def _validate_inputs_exist(paths: List[str]) -> None:
    missing = [p for p in paths if not os.path.isfile(p)]
    if missing:
        raise FileNotFoundError(f"input file(s) missing: {missing}")


def _pick_backends(reg, requested: str, prefer: Optional[List[str]] = None) -> List[str]:
    # Preferred order: explicit -> prefer list -> cpu-sim -> gpu-sim -> registry order
    discovered = []
    try:
        discovered = list(reg.list_backends())
    except Exception as e:
        _log.warning(f"module loader (spec) failed for '{name}': {e}")
    base = []
    if requested and requested != "auto":
        base = [requested]
    elif prefer:
        base = prefer[:]
    else:
        base = []
    # Add defaults if not already included
    for name in ["cpu-sim", "gpu-sim"]:
        if name not in base:
            base.append(name)
    # Append registry remainder
    for n in discovered:
        if n not in base:
            base.append(n)
    # Deduplicate while preserving order
    seen = set()
    order: List[str] = []
    for n in base:
        if n not in seen:
            order.append(n)
            seen.add(n)
    return order


def compile_and_run(
    graph: Any,
    backend: str = "auto",
    constraints: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Compile and execute an EIR graph on a selected backend.

    Args:
      graph: Either an EIR dict or a path to an EIR JSON file.
      backend: Backend name or "auto" to allow automatic selection.
      constraints: Optional dict with keys:
        - inputs: List[str] of Event Tensor JSONL input paths (required)
        - trace_out: str output JSONL path (required)
        - prefer_backends: List[str] preference override for auto selection
        - overrides: Dict for future extension (e.g., epsilon overrides)

    Returns:
      dict with fields:
        - status: "ok"
        - backend: selected backend name
        - plan: plan object (JSON-serializable)
        - run: backend run result (includes trace_path, count)
    """
    constraints = constraints or {}

    # Load dependencies
    validators = _load_validators()
    reg = _load_backend_registry()

    # Load EIR JSON
    if isinstance(graph, str):
        eir_path = graph
        try:
            eir_obj = validators.load_json(eir_path)
        except Exception as e:
            raise ValueError(f"cannot load EIR JSON '{eir_path}': {e}")
    elif isinstance(graph, dict):
        eir_obj = graph
    else:
        raise TypeError("graph must be a dict EIR object or a path to an EIR JSON file")

    # Validate EIR
    issues = validators.validate_eir(eir_obj)
    if issues:
        msgs = "; ".join(str(i) for i in issues)
        raise ValueError(f"EIR validation failed: {msgs}")

    # Inputs and trace_out
    inputs = _ensure_list(constraints.get("inputs"))
    if not inputs:
        raise ValueError("constraints.inputs is required and must contain at least one input path")
    _validate_inputs_exist(inputs)

    trace_out = constraints.get("trace_out")
    if not trace_out or not isinstance(trace_out, str):
        raise ValueError("constraints.trace_out is required (output JSONL path)")
    os.makedirs(os.path.dirname(trace_out) or ".", exist_ok=True)

    prefer_backends = constraints.get("prefer_backends")
    prefer_backends = list(prefer_backends) if isinstance(prefer_backends, (list, tuple)) else None

    backend_order = _pick_backends(reg, backend, prefer_backends)
    _log.info(f"backend selection order: {backend_order}")

    selected_name = None
    plan_obj: Dict[str, Any] = {}
    last_err: Optional[Exception] = None

    for name in backend_order:
        try:
            be = reg.load_backend(name)
            _log.info(f"trying backend '{name}' for planning")
            plan_obj = be.plan(eir_obj)
            selected_name = name
            _log.info(f"planning succeeded on backend '{name}'")
            # Execute
            run_res = be.run(eir_obj, inputs, trace_out, plan=plan_obj)
            _log.info(f"execution completed on backend '{name}'; trace: {run_res.get('trace_path')}")
            return {
                "status": "ok",
                "backend": selected_name,
                "plan": plan_obj,
                "run": run_res,
            }
        except Exception as e:
            _log.warning(f"backend '{name}' failed: {e}")
            last_err = e
            continue

    # If reached here, all backends failed to plan or run
    raise RuntimeError(f"no suitable backend could execute the graph; last error: {last_err}")
