#!/usr/bin/env python3
"""
EventFlow CLI

Phase 1 focus:
- Validators for EIR, Event Tensor (JSON/JSONL), DCD, EFPKG
- Deterministic, consistent error reporting with non-zero exit codes on validation failure

Phase 2 additions:
- SAL streaming command to normalize sensor inputs to Event Tensor JSONL

Phase 3 additions:
- cpu-sim backend planning and execution with golden trace capture

Phase 5 additions:
- Trace comparator for conformance (golden vs candidate)
"""

import argparse
import json
import os
import sys
import datetime
import types
import runpy
import logging
from typing import Any, List

# Global CLI flags
CLI_JSON = False

# Logger
_log = logging.getLogger("eventflow.cli")

# ------------------------------------------------------------
# Dynamic module loaders (avoid packaging issues during scaffold)
# ------------------------------------------------------------

def _base_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _load_module_with_fallback(path: str, name: str):
    """
    Robust module loader that tries:
      1) importlib.util.spec_from_file_location
      2) importlib.machinery.SourceFileLoader
      3) runpy.run_path into a fresh ModuleType
    """
    import importlib.util
    import importlib.machinery
    try:
        # Attempt 1: Standard spec/loader path
        spec = importlib.util.spec_from_file_location(name, path)
        if spec is not None and spec.loader is not None:
            try:
                mod = importlib.util.module_from_spec(spec)  # type: ignore
                spec.loader.exec_module(mod)  # type: ignore
                return mod
            except Exception as e:
                _log.warning(f"cli module loader (spec) failed for '{name}': {e}")

        # Attempt 2: SourceFileLoader explicit execution
        try:
            loader = importlib.machinery.SourceFileLoader(name, path)
            code = loader.get_code(name)
            mod = types.ModuleType(name)
            mod.__file__ = path  # type: ignore[attr-defined]
            exec(code, mod.__dict__)
            return mod
        except Exception as e:
            _log.warning(f"cli module loader (SourceFileLoader) failed for '{name}': {e}")

        # Attempt 3: runpy fallback
        ns = runpy.run_path(path)
        mod = types.ModuleType(name)
        mod.__file__ = path  # type: ignore[attr-defined]
        for k, v in ns.items():
            setattr(mod, k, v)
        return mod
    except Exception as e:
        raise RuntimeError(f"failed to load module '{name}' from {path}: {e}")


def _load_validators():
    vpath = os.path.join(_base_dir(), "eventflow-core", "validators.py")
    if not os.path.isfile(vpath):
        print(f"fatal: validators not found at {vpath}", file=sys.stderr)
        sys.exit(2)
    try:
        return _load_module_with_fallback(vpath, "eventflow_validators")
    except Exception as e:
        print(f"fatal: failed to load validators: {e}", file=sys.stderr)
        sys.exit(2)


def _load_sal():
    spath = os.path.join(_base_dir(), "eventflow-sal", "api.py")
    if not os.path.isfile(spath):
        print(f"fatal: SAL API not found at {spath}", file=sys.stderr)
        sys.exit(2)
    try:
        return _load_module_with_fallback(spath, "eventflow_sal_api")
    except Exception as e:
        print(f"fatal: failed to load SAL: {e}", file=sys.stderr)
        sys.exit(2)


def _load_backend_registry():
    rpath = os.path.join(_base_dir(), "eventflow-backends", "registry", "registry.py")
    if not os.path.isfile(rpath):
        print(f"fatal: backend registry not found at {rpath}", file=sys.stderr)
        sys.exit(2)
    try:
        return _load_module_with_fallback(rpath, "eventflow_backend_registry")
    except Exception as e:
        print(f"fatal: failed to load backend registry: {e}", file=sys.stderr)
        sys.exit(2)


def _load_comparator():
    cpath = os.path.join(_base_dir(), "eventflow-core", "conformance", "comparator.py")
    if not os.path.isfile(cpath):
        print(f"fatal: comparator not found at {cpath}", file=sys.stderr)
        sys.exit(2)
    try:
        return _load_module_with_fallback(cpath, "eventflow_conformance_comparator")
    except Exception as e:
        print(f"fatal: failed to load comparator: {e}", file=sys.stderr)
        sys.exit(2)


validators = _load_validators()

# ------------------------------------------------------------
# Common helpers
# ------------------------------------------------------------

def _print_issues(issues: List[Any]) -> None:
    # JSON output mode
    if "CLI_JSON" in globals() and globals().get("CLI_JSON"):
        msgs = []
        for i in issues:
            try:
                msgs.append(str(i))
            except Exception:
                msgs.append(repr(i))
        print(json.dumps({"ok": len(issues) == 0, "issues": msgs}, indent=2))
        return
    # Text output mode
    if not issues:
        print("OK")
        return
    print(f"FAIL ({len(issues)} issues):")
    for i in issues:
        try:
            print(" -", str(i))
        except Exception:
            print(" -", i)


def _read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ------------------------------------------------------------
# Basic info
# ------------------------------------------------------------

def cmd_version(_args: argparse.Namespace) -> None:
    if "CLI_JSON" in globals() and globals().get("CLI_JSON"):
        print(json.dumps({"version": "0.1.0"}))
    else:
        print("EventFlow SDK v0.1.0")


def cmd_list_backends(_args: argparse.Namespace) -> None:
    try:
        reg = _load_backend_registry()
        names = list(reg.list_backends())
    except SystemExit:
        # registry missing; fall back
        names = ["cpu-sim", "gpu-sim"]
    if "CLI_JSON" in globals() and globals().get("CLI_JSON"):
        print(json.dumps({"backends": names}, indent=2))
    else:
        for n in names:
            print(n)

# ------------------------------------------------------------
# Validators (Phase 1)
# ------------------------------------------------------------

def cmd_validate_eir(args: argparse.Namespace) -> None:
    path = args.path
    try:
        obj = _read_json(path)
    except Exception as e:
        print(f"error: cannot load EIR JSON '{path}': {e}", file=sys.stderr)
        sys.exit(2)
    issues = validators.validate_eir(obj)
    _print_issues(issues)
    sys.exit(0 if len(issues) == 0 else 1)


def cmd_validate_event(args: argparse.Namespace) -> None:
    path = args.path
    fmt = args.format
    if fmt == "auto":
        fmt = "jsonl" if path.lower().endswith(".jsonl") else "json"
    if fmt == "jsonl":
        issues = validators.validate_event_tensor_jsonl_path(path)
    elif fmt == "json":
        try:
            obj = _read_json(path)
        except Exception as e:
            print(f"error: cannot load Event Tensor JSON '{path}': {e}", file=sys.stderr)
            sys.exit(2)
        issues = validators.validate_event_tensor_json(obj)
    else:
        print(f"error: unknown format '{fmt}' (expected json|jsonl|auto)", file=sys.stderr)
        sys.exit(2)
    _print_issues(issues)
    sys.exit(0 if len(issues) == 0 else 1)


def cmd_validate_dcd(args: argparse.Namespace) -> None:
    path = args.path
    try:
        obj = _read_json(path)
    except Exception as e:
        print(f"error: cannot load DCD JSON '{path}': {e}", file=sys.stderr)
        sys.exit(2)
    issues = validators.validate_dcd(obj)
    _print_issues(issues)
    sys.exit(0 if len(issues) == 0 else 1)


def cmd_validate_efpkg(args: argparse.Namespace) -> None:
    manifest_path = args.manifest
    root = args.root or os.path.dirname(os.path.abspath(manifest_path))
    try:
        manifest = _read_json(manifest_path)
    except Exception as e:
        print(f"error: cannot load EFPKG manifest '{manifest_path}': {e}", file=sys.stderr)
        sys.exit(2)
    issues = validators.validate_efpkg(manifest, root_dir=root)
    _print_issues(issues)
    sys.exit(0 if len(issues) == 0 else 1)

# ------------------------------------------------------------
# Additional Validators
# ------------------------------------------------------------

def cmd_validate_trace(args: argparse.Namespace) -> None:
    path = args.path
    issues = validators.validate_event_tensor_jsonl_path(path)
    _print_issues(issues)
    sys.exit(0 if len(issues) == 0 else 1)

# ------------------------------------------------------------
# SAL Streaming (Phase 2)
# ------------------------------------------------------------

def cmd_sal_stream(args: argparse.Namespace) -> None:
    sal = _load_sal()
    uri = args.uri
    out = args.out
    kwargs: dict[str, Any] = {}
    if args.sample_rate is not None: kwargs["sample_rate"] = args.sample_rate
    if args.window_ms is not None: kwargs["window_ms"] = args.window_ms
    if args.hop_ms is not None: kwargs["hop_ms"] = args.hop_ms
    if args.bands is not None: kwargs["bands"] = args.bands
    if args.rate_limit_keps is not None: kwargs["rate_limit_keps"] = args.rate_limit_keps
    if args.overflow_policy is not None: kwargs["overflow_policy"] = args.overflow_policy
    if getattr(args, "telemetry_out", None): kwargs["telemetry_out"] = args.telemetry_out
    try:
        tele = sal.stream_to_jsonl(uri, out, **kwargs)
        if CLI_JSON:
            print(json.dumps({"out": out, "telemetry": tele}, indent=2))
        else:
            print(f"wrote: {out}")
    except Exception as e:
        print(f"error: sal-stream failed: {e}", file=sys.stderr)
        sys.exit(1)
# ------------------------------------------------------------
# Profiling (Phase 4)
# ------------------------------------------------------------

def cmd_profile(args: argparse.Namespace) -> None:
    path = args.path
    try:
        from collections import Counter
        with open(path, "r", encoding="utf-8") as f:
            header_line = f.readline()
            if not header_line:
                print(f"error: empty file '{path}'", file=sys.stderr)
                sys.exit(2)
            obj = json.loads(header_line)
            if "header" not in obj:
                print(f"error: first line must contain 'header' object in '{path}'", file=sys.stderr)
                sys.exit(2)
            header = obj["header"]
            unit = header.get("units", {}).get("time", "us")
            dims = list(header.get("dims", []) or [])
            first_dim = dims[0] if dims else None

            tmin = None
            tmax = None
            count = 0
            vmin = float("inf")
            vmax = float("-inf")
            vsum = 0.0
            # Delta time stats
            tprev = None
            dt_list: List[int] = []
            # Channel histogram (based on first index)
            ch_counter: Counter[int] = Counter()

            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                ts = int(rec["ts"])
                idx = rec.get("idx", [])
                val = float(rec.get("val", 0.0))

                count += 1
                if tmin is None or ts < tmin:
                    tmin = ts
                if tmax is None or ts > tmax:
                    tmax = ts
                if tprev is not None:
                    dt_list.append(ts - tprev)
                tprev = ts

                if val < vmin:
                    vmin = val
                if val > vmax:
                    vmax = val
                vsum += val

                if isinstance(idx, list) and len(idx) > 0:
                    try:
                        ch_counter[int(idx[0])] += 1
                    except Exception as e:
                        _log.warning(f"failed to parse channel index from record: {rec}, error: {e}")

            duration_native = 0 if (tmin is None or tmax is None) else (tmax - tmin)
            to_us = {"ns": 0.001, "us": 1.0, "ms": 1000.0}
            duration_us = int(round(duration_native * to_us.get(unit, 1.0)))
            eps = (count / (duration_us / 1_000_000.0)) if duration_us > 0 else 0.0

            # dt stats
            dt_count = len(dt_list)
            if dt_count > 0:
                dts_sorted = sorted(dt_list)
                mean_dt = sum(dt_list) / float(dt_count)
                p50_dt = dts_sorted[dt_count // 2]
                p95_dt = dts_sorted[int(dt_count * 0.95) if dt_count > 1 else 0]
            else:
                mean_dt = 0.0
                p50_dt = 0
                p95_dt = 0

            top_channels = [{"channel": k, "count": v} for k, v in ch_counter.most_common(10)]

            out = {
                "path": path,
                "count": count,
                "time_unit": unit,
                "ts_min": tmin,
                "ts_max": tmax,
                "duration_native": duration_native,
                "duration_us": duration_us,
                "events_per_second": eps,
                "val_min": None if count == 0 else vmin,
                "val_max": None if count == 0 else vmax,
                "val_mean": None if count == 0 else (vsum / count),
                "dt": {
                    "count": dt_count,
                    "mean": mean_dt,
                    "p50": p50_dt,
                    "p95": p95_dt,
                },
                "first_dim": first_dim,
                "top_channels": top_channels,
                "header": header,
            }
            print(json.dumps(out, indent=2))
            sys.exit(0)
    except FileNotFoundError:
        print(f"error: file not found '{path}'", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"error: profiling failed: {e}", file=sys.stderr)
        sys.exit(1)

# ------------------------------------------------------------
# Packaging (Phase 4)
# ------------------------------------------------------------

def cmd_package(args: argparse.Namespace) -> None:
    eir_path = args.eir
    golden_path = args.golden
    inputs = args.input or []
    out_path = args.out
    model_id = args.model_id
    model_name = args.model_name
    model_version = getattr(args, "model_version", None)
    model_description = getattr(args, "model_description", None)
    try:
        eir_obj = _read_json(eir_path)
    except Exception as e:
        print(f"error: cannot load EIR JSON '{eir_path}': {e}", file=sys.stderr)
        sys.exit(2)
    # Validate EIR
    issues = validators.validate_eir(eir_obj)
    if issues:
        _print_issues(issues)
        sys.exit(1)
    # Paths
    root = os.path.dirname(os.path.abspath(out_path))
    os.makedirs(root, exist_ok=True)
    def _rel(p: str) -> str:
        ap = os.path.abspath(p)
        try:
            return os.path.relpath(ap, start=root)
        except Exception:
            return ap
    # Determinism from EIR
    time_cfg = eir_obj.get("time", {})
    determinism = {
        "time_unit": time_cfg.get("unit", "us"),
        "mode": time_cfg.get("mode", "exact_event"),
        "epsilon_time_us": time_cfg.get("epsilon_time_us", 100),
        "epsilon_numeric": time_cfg.get("epsilon_numeric", 1e-5),
        "seed": eir_obj.get("seed", 0),
    }
    if determinism["mode"] == "fixed_step":
        determinism["fixed_step_dt_us"] = time_cfg.get("fixed_step_dt_us", 100)
    # Artifacts
    eir_rel = _rel(eir_path)
    golden_rel = _rel(golden_path)
    man = {
        "schema_version": "0.1.0",
        "sdk_version": "0.1.0",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "model": {
            "id": model_id,
            "name": model_name,
        },
        "profile": {"name": eir_obj.get("profile", "BASE")},
        "determinism": determinism,
        "features": [],
        "capabilities_required": {},
        "artifacts": {
            "eir": {
                "path": eir_rel,
                "format": "json",
                "sha256": validators.hash_sha256_file(os.path.join(root, eir_rel)),
                "filesize_bytes": os.path.getsize(os.path.join(root, eir_rel)) if os.path.exists(os.path.join(root, eir_rel)) else os.path.getsize(eir_path),
            },
            "traces": {
                "golden": {
                    "path": golden_rel,
                    "format": "jsonl",
                    "sha256": validators.hash_sha256_file(os.path.join(root, golden_rel)),
                },
                "inputs": [
                    {
                        "path": _rel(p),
                        "format": "jsonl",
                        "sha256": validators.hash_sha256_file(os.path.join(root, _rel(p))),
                    }
                    for p in inputs
                ] if inputs else [],
            },
        },
        "compatibility": {},
    }
    if model_version:
        man["model"]["version"] = model_version
    if model_description:
        man["model"]["description"] = model_description
    # Validate manifest
    issues2 = validators.validate_efpkg(man, root_dir=root)
    if issues2:
        _print_issues(issues2)
        sys.exit(1)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(man, f, indent=2)
    if "CLI_JSON" in globals() and globals().get("CLI_JSON"):
        print(json.dumps({"manifest": out_path, "artifacts": man.get("artifacts", {})}, indent=2))
    else:
        print(f"manifest written: {out_path}")
    sys.exit(0)

# ------------------------------------------------------------
# Planning and Execution (Phase 3)
# ------------------------------------------------------------


def cmd_build(args: argparse.Namespace) -> None:
    """Plan execution for a backend using an EIR JSON."""
    backend_name = args.backend
    eir_path = args.eir
    out_plan = args.plan_out
    try:
        eir_obj = _read_json(eir_path)
    except Exception as e:
        print(f"error: cannot load EIR JSON '{eir_path}': {e}", file=sys.stderr)
        sys.exit(2)
    # Validate EIR first
    issues = validators.validate_eir(eir_obj)
    if issues:
        _print_issues(issues)
        sys.exit(1)
    reg = _load_backend_registry()
    backend = reg.load_backend(backend_name)
    try:
        plan = backend.plan(eir_obj)
    except Exception as e:
        print(f"error: planning failed: {e}", file=sys.stderr)
        sys.exit(1)
    if out_plan:
        with open(out_plan, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2)
        print(f"plan written: {out_plan}")
    else:
        print(json.dumps(plan, indent=2))
    sys.exit(0)


def cmd_run(args: argparse.Namespace) -> None:
    """Execute a plan (or plan-on-the-fly) on a backend and emit a golden trace."""
    backend_name = args.backend
    eir_path = args.eir
    inputs = args.input or []
    trace_out = args.trace_out
    plan_in = args.plan
    if not inputs:
        print("error: at least one --input is required", file=sys.stderr)
        sys.exit(2)
    try:
        eir_obj = _read_json(eir_path)
    except Exception as e:
        print(f"error: cannot load EIR JSON '{eir_path}': {e}", file=sys.stderr)
        sys.exit(2)
    reg = _load_backend_registry()
    backend = reg.load_backend(backend_name)
    plan = None
    if plan_in:
        try:
            plan = _read_json(plan_in)
        except Exception as e:
            print(f"error: cannot load plan JSON '{plan_in}': {e}", file=sys.stderr)
            sys.exit(2)
    try:
        result = backend.run(eir_obj, inputs, trace_out, plan=plan)
    except Exception as e:
        print(f"error: backend run failed: {e}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, indent=2))
    sys.exit(0)

# ------------------------------------------------------------
# Trace comparator (Phase 5)
# ------------------------------------------------------------

def cmd_compare_traces(args: argparse.Namespace) -> None:
    comp = _load_comparator()
    res = comp.compare_traces_jsonl(
        golden_path=args.golden,
        candidate_path=args.candidate,
        eps_time_us=args.eps_time_us,
        eps_numeric=args.eps_numeric,
    )
    if CLI_JSON:
        print(json.dumps(res, indent=2))
    else:
        comp.print_report(res)
    sys.exit(0 if res.get("ok") else 1)

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(prog="ef", description="EventFlow CLI")
    p.add_argument("--json", action="store_true", help="Emit JSON output where supported")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("version", help="Print EventFlow SDK version")
    s.set_defaults(func=cmd_version)

    s = sub.add_parser("list-backends", help="List discovered backends")
    s.set_defaults(func=cmd_list_backends)

    # Validators
    s = sub.add_parser("validate-eir", help="Validate an EIR JSON document")
    s.add_argument("--path", required=True, help="Path to EIR JSON")
    s.set_defaults(func=cmd_validate_eir)

    s = sub.add_parser("validate-event", help="Validate an Event Tensor file (JSON or JSONL)")
    s.add_argument("--path", required=True, help="Path to Event Tensor file")
    s.add_argument("--format", choices=["auto", "json", "jsonl"], default="auto", help="Input format (default: auto)")
    s.set_defaults(func=cmd_validate_event)

    s = sub.add_parser("validate-dcd", help="Validate a Device Capability Descriptor (DCD) JSON")
    s.add_argument("--path", required=True, help="Path to DCD JSON")
    s.set_defaults(func=cmd_validate_dcd)

    se = sub.add_parser("validate-efpkg", help="Validate an EventFlow package manifest and referenced artifacts")
    se.add_argument("--manifest", required=True, help="Path to EFPKG manifest (JSON or YAML-as-JSON)")
    se.add_argument("--root", required=False, help="Root directory for relative artifact paths (default: manifest dir)")
    se.set_defaults(func=cmd_validate_efpkg)

    # Validate Event Tensor JSONL trace (header + records)
    st = sub.add_parser("validate-trace", help="Validate an Event Tensor JSONL trace")
    st.add_argument("--path", required=True, help="Path to Event Tensor JSONL")
    st.set_defaults(func=cmd_validate_trace)

    # SAL streaming
    s = sub.add_parser("sal-stream", help="Normalize a SAL URI source to Event Tensor JSONL")
    s.add_argument("--uri", required=True, help="SAL URI, e.g., vision.dvs://file?format=jsonl&path=/data/events.jsonl OR audio.mic://file?path=/data/audio.wav")
    s.add_argument("--out", required=True, help="Output JSONL file path")
    s.add_argument("--sample-rate", type=int, help="Audio sample rate (Hz)")
    s.add_argument("--window-ms", type=int, help="Audio STFT window size (ms)")
    s.add_argument("--hop-ms", type=int, help="Audio STFT hop (ms)")
    s.add_argument("--bands", type=int, help="Audio band count for aggregation")
    s.add_argument("--rate-limit-keps", type=int, help="Rate limit in kilo-events per second (per channel)")
    s.add_argument("--overflow-policy", choices=["drop_head", "drop_tail", "block"], help="Overflow policy")
    s.add_argument("--telemetry-out", help="Optional path to write SAL telemetry JSON")
    s.set_defaults(func=cmd_sal_stream)

    # Profiling
    s = sub.add_parser("profile", help="Profile an Event Tensor JSONL file")
    s.add_argument("--path", required=True, help="Path to Event Tensor JSONL")
    s.set_defaults(func=cmd_profile)

    # Packaging
    # Trace analysis alias
    s = sub.add_parser("trace-stats", help="Compute statistics for an Event Tensor JSONL trace (alias of 'profile')")
    s.add_argument("--path", required=True, help="Path to Event Tensor JSONL")
    s.set_defaults(func=cmd_profile)
    s = sub.add_parser("package", help="Create an EFPKG manifest for deployment")
    s.add_argument("--eir", required=True, help="Path to EIR JSON")
    s.add_argument("--golden", required=True, help="Golden trace JSONL path")
    s.add_argument("--input", action="append", help="Input Event Tensor JSONL (repeatable)")
    s.add_argument("--model-id", required=True, help="Model identifier")
    s.add_argument("--model-name", required=True, help="Human-friendly model name")
    s.add_argument("--model-version", required=False, help="Model version string")
    s.add_argument("--model-description", required=False, help="Model description")
    s.add_argument("--out", required=True, help="Output manifest path (.json)")
    s.set_defaults(func=cmd_package)
    # Planning & execution
    s = sub.add_parser("build", help="Plan execution for a target backend")
    s.add_argument("--eir", required=True, help="Path to EIR JSON")
    s.add_argument("--backend", default="cpu-sim", help="Backend name (default: cpu-sim)")
    s.add_argument("--plan-out", required=False, help="Write plan JSON to this path")
    s.set_defaults(func=cmd_build)

    s = sub.add_parser("run", help="Run a plan on a selected backend and emit a golden trace")
    s.add_argument("--eir", required=True, help="Path to EIR JSON")
    s.add_argument("--backend", default="cpu-sim", help="Backend name (default: cpu-sim)")
    s.add_argument("--input", action="append", help="Input Event Tensor JSONL (repeatable)", required=True)
    s.add_argument("--trace-out", required=True, help="Output golden trace JSONL path")
    s.add_argument("--plan", required=False, help="Path to plan JSON (optional; if omitted, plan is computed)")
    s.set_defaults(func=cmd_run)

    # Trace comparator
    s = sub.add_parser("compare-traces", help="Compare two traces for equivalence under epsilons")
    s.add_argument("--golden", required=True, help="Golden trace JSONL path")
    s.add_argument("--candidate", required=True, help="Candidate trace JSONL path")
    s.add_argument("--eps-time-us", type=int, default=100, help="Time epsilon (microseconds)")
    s.add_argument("--eps-numeric", type=float, default=1e-5, help="Numeric epsilon (relative)")
    s.set_defaults(func=cmd_compare_traces)

    args = p.parse_args()
    global CLI_JSON
    CLI_JSON = bool(getattr(args, "json", False))
    args.func(args)


if __name__ == "__main__":
    main()
