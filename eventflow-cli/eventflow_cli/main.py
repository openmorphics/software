from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from typing import Any, List, Optional
from .license_gate import requires_license


CLI_JSON = False


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _ensure_repo_paths() -> None:
    """Allow running via repo-local launcher without editable installs."""
    root = _repo_root()
    for rel in ("eventflow-core", "eventflow-sal", "eventflow-backends", "eventflow-hub"):
        path = os.path.join(root, rel)
        if path not in sys.path:
            sys.path.insert(0, path)


def _emit_json(obj: Any) -> None:
    print(json.dumps(obj, indent=2))


def _fail(message: str, exit_code: int) -> None:
    if CLI_JSON:
        _emit_json({"ok": False, "error": message})
    else:
        print(f"error: {message}", file=sys.stderr)
    sys.exit(exit_code)


def _print_issues(issues: List[Any]) -> None:
    if CLI_JSON:
        _emit_json({"ok": len(issues) == 0, "issues": [str(i) for i in issues]})
        return
    if not issues:
        print("OK")
        return
    print(f"FAIL ({len(issues)} issues):")
    for issue in issues:
        print(" -", str(issue))


def _read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def cmd_version(_args: argparse.Namespace) -> None:
    if CLI_JSON:
        _emit_json({"version": "0.2.0"})
    else:
        print("EventFlow SDK v0.2.0")
    sys.exit(0)


def cmd_list_backends(_args: argparse.Namespace) -> None:
    _ensure_repo_paths()
    try:
        from eventflow_backends import list_backends

        names = list(list_backends())
    except Exception:
        names = ["cpu-sim", "gpu-sim"]

    if CLI_JSON:
        _emit_json({"backends": names})
    else:
        for name in names:
            print(name)
    sys.exit(0)


def cmd_validate(args: argparse.Namespace) -> None:
    _ensure_repo_paths()
    try:
        from eventflow_core import validators
    except Exception as e:
        _fail(f"failed to import validators: {e}", 2)

    targets = {
        "eir": args.eir,
        "event": args.event,
        "trace": args.trace,
        "dcd": args.dcd,
        "efpkg": args.efpkg,
    }
    selected = [name for name, value in targets.items() if value]
    if len(selected) != 1:
        _fail("exactly one target is required (--eir|--event|--trace|--dcd|--efpkg)", 2)
    mode = selected[0]

    try:
        if mode == "eir":
            issues = validators.validate_eir(_read_json(args.eir))
        elif mode == "event":
            fmt = args.format
            if fmt == "auto":
                fmt = "jsonl" if args.event.lower().endswith(".jsonl") else "json"
            if fmt == "jsonl":
                issues = validators.validate_event_tensor_jsonl_path(args.event)
            elif fmt == "json":
                issues = validators.validate_event_tensor_json(_read_json(args.event))
            else:
                _fail(f"unknown format '{fmt}'", 2)
        elif mode == "trace":
            issues = validators.validate_event_tensor_jsonl_path(args.trace)
        elif mode == "dcd":
            issues = validators.validate_dcd(_read_json(args.dcd))
        else:
            manifest = _read_json(args.efpkg)
            root = args.root or os.path.dirname(os.path.abspath(args.efpkg))
            issues = validators.validate_efpkg(manifest, root_dir=root)
    except FileNotFoundError as e:
        _fail(f"file not found: {e}", 2)
    except json.JSONDecodeError as e:
        _fail(f"invalid JSON: {e}", 2)
    except Exception as e:
        _fail(f"validation failed: {e}", 1)

    _print_issues(issues)
    sys.exit(0 if len(issues) == 0 else 1)


def cmd_sal_stream(args: argparse.Namespace) -> None:
    _ensure_repo_paths()
    try:
        from eventflow_sal.stream import stream_to_jsonl
    except Exception as e:
        _fail(f"failed to import SAL stream API: {e}", 2)

    kwargs: dict[str, Any] = {}
    if args.sample_rate is not None:
        kwargs["sample_rate"] = args.sample_rate
    if args.window_ms is not None:
        kwargs["window_ms"] = args.window_ms
    if args.hop_ms is not None:
        kwargs["hop_ms"] = args.hop_ms
    if args.bands is not None:
        kwargs["bands"] = args.bands
    if args.rate_limit_keps is not None:
        kwargs["rate_limit_keps"] = args.rate_limit_keps
    if args.overflow_policy is not None:
        kwargs["overflow_policy"] = args.overflow_policy
    if args.telemetry_out:
        kwargs["telemetry_out"] = args.telemetry_out

    try:
        tele = stream_to_jsonl(args.uri, args.out, **kwargs)
    except FileNotFoundError as e:
        _fail(str(e), 2)
    except Exception as e:
        _fail(f"sal-stream failed: {e}", 1)

    if CLI_JSON:
        _emit_json({"out": args.out, "telemetry": tele})
    else:
        print(f"wrote: {args.out}")
    sys.exit(0)


def cmd_profile(args: argparse.Namespace) -> None:
    path = args.path
    try:
        from collections import Counter

        with open(path, "r", encoding="utf-8") as f:
            header_line = f.readline()
            if not header_line:
                _fail(f"empty file '{path}'", 2)
            obj = json.loads(header_line)
            if "header" not in obj:
                _fail(f"first line must contain 'header' object in '{path}'", 2)
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
            tprev = None
            dt_list: List[int] = []
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
                    ch_counter[int(idx[0])] += 1

            duration_native = 0 if (tmin is None or tmax is None) else (tmax - tmin)
            to_us = {"ns": 0.001, "us": 1.0, "ms": 1000.0}
            duration_us = int(round(duration_native * to_us.get(unit, 1.0)))
            eps = (count / (duration_us / 1_000_000.0)) if duration_us > 0 else 0.0

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
            _emit_json(out)
            sys.exit(0)
    except FileNotFoundError:
        _fail(f"file not found '{path}'", 2)
    except Exception as e:
        _fail(f"profiling failed: {e}", 1)


def cmd_package(args: argparse.Namespace) -> None:
    _ensure_repo_paths()
    try:
        from eventflow_core import validators
    except Exception as e:
        _fail(f"failed to import validators: {e}", 2)

    try:
        eir_obj = _read_json(args.eir)
    except Exception as e:
        _fail(f"cannot load EIR JSON '{args.eir}': {e}", 2)

    issues = validators.validate_eir(eir_obj)
    if issues:
        _print_issues(issues)
        sys.exit(1)

    root = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(root, exist_ok=True)

    def _rel(path: str) -> str:
        return os.path.relpath(os.path.abspath(path), start=root)

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

    man = {
        "schema_version": "0.1.0",
        "sdk_version": "0.1.0",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "model": {
            "id": args.model_id,
            "name": args.model_name,
        },
        "profile": {"name": eir_obj.get("profile", "BASE")},
        "determinism": determinism,
        "features": [],
        "capabilities_required": {},
        "artifacts": {
            "eir": {
                "path": _rel(args.eir),
                "format": "json",
                "sha256": validators.hash_sha256_file(args.eir),
                "filesize_bytes": os.path.getsize(args.eir),
            },
            "traces": {
                "golden": {
                    "path": _rel(args.golden),
                    "format": "jsonl",
                    "sha256": validators.hash_sha256_file(args.golden),
                },
                "inputs": [
                    {
                        "path": _rel(p),
                        "format": "jsonl",
                        "sha256": validators.hash_sha256_file(p),
                    }
                    for p in (args.input or [])
                ],
            },
        },
        "compatibility": {},
    }
    if args.model_version:
        man["model"]["version"] = args.model_version
    if args.model_description:
        man["model"]["description"] = args.model_description

    issues = validators.validate_efpkg(man, root_dir=root)
    if issues:
        _print_issues(issues)
        sys.exit(1)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(man, f, indent=2)

    if CLI_JSON:
        _emit_json({"manifest": args.out, "artifacts": man.get("artifacts", {})})
    else:
        print(f"manifest written: {args.out}")
    sys.exit(0)


def cmd_build(args: argparse.Namespace) -> None:
    _ensure_repo_paths()
    try:
        from eventflow_core.validators import validate_eir
        from eventflow_backends import load_backend
    except Exception as e:
        _fail(f"failed to load dependencies: {e}", 2)

    try:
        eir_obj = _read_json(args.eir)
    except Exception as e:
        _fail(f"cannot load EIR JSON '{args.eir}': {e}", 2)

    issues = validate_eir(eir_obj)
    if issues:
        _print_issues(issues)
        sys.exit(1)

    try:
        backend = load_backend(args.backend)
        plan = backend.plan(eir_obj)
    except Exception as e:
        _fail(f"planning failed: {e}", 1)

    if args.plan_out:
        with open(args.plan_out, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2)
        if CLI_JSON:
            _emit_json({"plan_out": args.plan_out})
        else:
            print(f"plan written: {args.plan_out}")
    else:
        _emit_json(plan)
    sys.exit(0)


def cmd_run(args: argparse.Namespace) -> None:
    _ensure_repo_paths()
    try:
        from eventflow_backends import load_backend
    except Exception as e:
        _fail(f"failed to load backend registry: {e}", 2)

    if not args.input:
        _fail("at least one --input is required", 2)

    try:
        eir_obj = _read_json(args.eir)
    except Exception as e:
        _fail(f"cannot load EIR JSON '{args.eir}': {e}", 2)

    plan = None
    if args.plan:
        try:
            plan = _read_json(args.plan)
        except Exception as e:
            _fail(f"cannot load plan JSON '{args.plan}': {e}", 2)

    try:
        backend = load_backend(args.backend)
        result = backend.run(eir_obj, args.input, args.trace_out, plan=plan)
    except Exception as e:
        _fail(f"backend run failed: {e}", 1)

    _emit_json(result)
    sys.exit(0)


def cmd_compare_traces(args: argparse.Namespace) -> None:
    _ensure_repo_paths()
    try:
        from eventflow_core.conformance.comparator import compare_traces_jsonl, print_report
    except Exception as e:
        _fail(f"failed to import comparator: {e}", 2)

    try:
        res = compare_traces_jsonl(
            golden_path=args.golden,
            candidate_path=args.candidate,
            eps_time_us=args.eps_time_us,
            eps_numeric=args.eps_numeric,
        )
    except FileNotFoundError as e:
        _fail(str(e), 2)
    except Exception as e:
        _fail(f"compare-traces failed: {e}", 1)

    if CLI_JSON:
        _emit_json(res)
    else:
        print_report(res)
    sys.exit(0 if res.get("ok") else 1)


@requires_license("conformance", tier="Pro")
def cmd_verify_conformance(args: argparse.Namespace) -> None:
    _ensure_repo_paths()
    if "eventflow_conformance" not in sys.modules:
        # Lazy import
        try:
            import eventflow_conformance
        except ImportError:
            _fail("eventflow-conformance package not found. It is required for this command.", 1)

    from eventflow_conformance import ConformanceValidator, EvidenceExporter
    from eventflow_license import LicenseValidator

    eir_path = args.eir
    if not os.path.exists(eir_path):
        _fail(f"EIR file not found: {eir_path}", 2)

    try:
        with open(eir_path, "r") as f:
            eir_data = json.load(f)
    except Exception as e:
        _fail(f"failed to read EIR: {e}", 2)

    validator = ConformanceValidator(args.cert_profile)
    violations = validator.validate(eir_data)

    license_val = LicenseValidator()
    org_name = license_val.get_status().get("org", "Unknown")

    exporter = EvidenceExporter(eir_path)
    report = exporter.generate_report(
        profile=args.cert_profile,
        violations=violations,
        backend_info={"name": "cli-verifier"},
        org_name=org_name
    )

    if args.evidence_out:
        exporter.export(report, args.evidence_out)

    if CLI_JSON:
        _emit_json({
            "ok": len(violations) == 0,
            "profile": args.cert_profile,
            "violations": violations,
            "report": report if not args.evidence_out else None,
            "evidence_path": args.evidence_out
        })
    else:
        if not violations:
            print(f"Conformance check PASSED for profile {args.cert_profile}")
        else:
            print(f"Conformance check FAILED for profile {args.cert_profile}:")
            for v in violations:
                print(f"  - {v}")
        if args.evidence_out:
            print(f"Evidence report exported to: {args.evidence_out}")


def cmd_hub(args: argparse.Namespace) -> None:
    from . import hub

    hub.handle(args, json_output=CLI_JSON)


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ef", description="EventFlow CLI")
    p.add_argument("--json", action="store_true", help="Emit JSON output where supported")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("version", help="Print EventFlow SDK version")
    s.set_defaults(func=cmd_version)

    s = sub.add_parser("list-backends", help="List discovered backends")
    s.set_defaults(func=cmd_list_backends)

    s = sub.add_parser("validate", help="Validate EventFlow artifacts")
    s.add_argument("--eir", help="Path to EIR JSON")
    s.add_argument("--event", help="Path to Event Tensor file (JSON or JSONL)")
    s.add_argument("--trace", help="Path to Event Tensor JSONL trace")
    s.add_argument("--dcd", help="Path to Device Capability Descriptor JSON")
    s.add_argument("--efpkg", help="Path to EFPKG manifest JSON")
    s.add_argument("--root", help="Root directory for EFPKG relative artifacts")
    s.add_argument("--format", choices=["auto", "json", "jsonl"], default="auto", help="Format for --event")
    s.set_defaults(func=cmd_validate)

    s = sub.add_parser("sal-stream", help="Normalize a SAL URI source to Event Tensor JSONL")
    s.add_argument("--uri", required=True, help="SAL URI")
    s.add_argument("--out", required=True, help="Output JSONL file path")
    s.add_argument("--sample-rate", type=int, help="Audio sample rate (Hz)")
    s.add_argument("--window-ms", type=int, help="Audio STFT window size (ms)")
    s.add_argument("--hop-ms", type=int, help="Audio STFT hop (ms)")
    s.add_argument("--bands", type=int, help="Audio band count")
    s.add_argument("--rate-limit-keps", type=int, help="Rate limit in kilo-events per second")
    s.add_argument("--overflow-policy", choices=["drop_head", "drop_tail", "block"], help="Overflow policy")
    s.add_argument("--telemetry-out", help="Optional path to write SAL telemetry JSON")
    s.set_defaults(func=cmd_sal_stream)

    s = sub.add_parser("profile", help="Profile an Event Tensor JSONL file")
    s.add_argument("--path", required=True, help="Path to Event Tensor JSONL")
    s.set_defaults(func=cmd_profile)

    s = sub.add_parser("trace-stats", help="Alias of profile")
    s.add_argument("--path", required=True, help="Path to Event Tensor JSONL")
    s.set_defaults(func=cmd_profile)

    s = sub.add_parser("package", help="Create an EFPKG manifest")
    s.add_argument("--eir", required=True, help="Path to EIR JSON")
    s.add_argument("--golden", required=True, help="Golden trace JSONL path")
    s.add_argument("--input", action="append", help="Input Event Tensor JSONL (repeatable)")
    s.add_argument("--model-id", required=True, help="Model identifier")
    s.add_argument("--model-name", required=True, help="Model name")
    s.add_argument("--model-version", help="Model version")
    s.add_argument("--model-description", help="Model description")
    s.add_argument("--out", required=True, help="Output manifest path")
    s.set_defaults(func=cmd_package)

    s = sub.add_parser("build", help="Plan execution for a target backend")
    s.add_argument("--eir", required=True, help="Path to EIR JSON")
    s.add_argument("--backend", default="cpu-sim", help="Backend name")
    s.add_argument("--plan-out", help="Write plan JSON to this path")
    s.set_defaults(func=cmd_build)

    s = sub.add_parser("run", help="Run on a backend and emit a trace")
    s.add_argument("--eir", required=True, help="Path to EIR JSON")
    s.add_argument("--backend", default="cpu-sim", help="Backend name")
    s.add_argument("--input", action="append", required=True, help="Input Event Tensor JSONL (repeatable)")
    s.add_argument("--trace-out", required=True, help="Output trace JSONL path")
    s.add_argument("--plan", help="Optional plan JSON path")
    s.set_defaults(func=cmd_run)

    s = sub.add_parser("compare-traces", help="Compare two traces for equivalence")
    s.add_argument("--golden", required=True, help="Golden trace JSONL path")
    s.add_argument("--candidate", required=True, help="Candidate trace JSONL path")
    s.add_argument("--eps-time-us", type=int, default=100, help="Time epsilon (microseconds)")
    s.add_argument("--eps-numeric", type=float, default=1e-5, help="Numeric epsilon")
    s.set_defaults(func=cmd_compare_traces)

    from . import hub

    hub_parser = sub.add_parser("hub", help="EventFlow Hub package management")
    hub.add_hub_subparser(hub_parser)
    hub_parser.set_defaults(func=cmd_hub)

    # Conformance
    p_conf = sub.add_parser("verify-conformance", help="[PRO] Verify graph conformance and export evidence")
    p_conf.add_argument("--eir", required=True, help="Path to EIR JSON")
    p_conf.add_argument("--cert-profile", default="BASE", help="Certification profile (BASE|AUTOMOTIVE_ISO26262|MEDICAL_IEC62304)")
    p_conf.add_argument("--evidence-out", help="Path to export evidence JSON report")
    p_conf.set_defaults(func=cmd_verify_conformance)

    return p


def main(argv: Optional[List[str]] = None) -> None:
    global CLI_JSON
    parser = make_parser()
    args = parser.parse_args(argv)
    CLI_JSON = bool(getattr(args, "json", False))
    args.func(args)


if __name__ == "__main__":
    main()
