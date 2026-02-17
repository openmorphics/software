"""
cpu-sim backend executor v0.1

Provides:
- plan_cpu_sim(eir, dcd) -> plan dict
- run_cpu_sim(plan, inputs_jsonl, out_trace_path) -> run result dict

This is a deterministic, minimal executor focusing on canonical ordering and trace capture.
It does not implement full spiking dynamics; it merges input Event Tensor streams and emits
a golden trace using canonical ordering. This satisfies Phase 3 baseline requirements for
deterministic replay and trace generation.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple

SCHEMA_VERSION = "0.1.0"


def _canonical_key(rec: Tuple[int, List[int], float]) -> tuple:
    ts, idx, _ = rec
    return (ts, tuple(idx or []))


def _write_header(fh, dims: List[str], units_value: str, meta: Dict[str, Any]) -> None:
    header = {
        "schema_version": SCHEMA_VERSION,
        "dims": dims,
        "units": {"time": "us", "value": units_value},
        "dtype": "f32",
        "layout": "coo",
        "metadata": meta,
    }
    fh.write(json.dumps({"header": header}) + "\n")


def _write_rec(fh, ts: int, idx: List[int], val: float) -> None:
    fh.write(json.dumps({"ts": ts, "idx": idx, "val": float(val)}) + "\n")


def plan_cpu_sim(eir: Dict[str, Any], dcd: Dict[str, Any]) -> Dict[str, Any]:
    """
    Capability negotiation v0.1:
    - Validate profile against DCD
    - Enforce timing epsilon contracts vs device time resolution
    - Select/quantize fixed_step dt_us when needed
    - Report unsupported ops as emulated
    - Surface overflow policy substitutions
    """
    time_cfg = eir.get("time", {}) or {}
    mode = time_cfg.get("mode", "exact_event")
    dt_us_req = time_cfg.get("fixed_step_dt_us")
    eps_time_us = time_cfg.get("epsilon_time_us", 100)
    eps_numeric = time_cfg.get("epsilon_numeric", 1e-5)

    warnings: List[str] = []
    negotiation: Dict[str, Any] = {"time": {}, "profile": {}, "ops": {}, "policies": {}}

    # DCD fields
    supported_ops = set(dcd.get("supported_ops", []) or [])
    deterministic_modes = set(dcd.get("deterministic_modes", []) or [])
    profiles = set(dcd.get("conformance_profiles", []) or [])
    time_resolution_ns = int(dcd.get("time_resolution_ns", 1000))
    res_us = time_resolution_ns / 1000.0
    clock = dcd.get("clock", {}) or {}
    fixed_only = bool(clock.get("deterministic_fixed_step_only", False))

    # Profile compatibility (fatal)
    prof = eir.get("profile")
    negotiation["profile"] = {"eir_profile": prof, "supported": bool(prof in profiles)}
    if prof and prof not in profiles:
        raise ValueError("backend.unsupported_profile: profile not supported by backend DCD")

    # Time mode support (warn + emulate in simulator)
    if mode not in deterministic_modes or (mode == "exact_event" and fixed_only):
        warnings.append(f"backend does not support time.mode='{mode}' deterministically; will emulate in simulator")

    # Time quantization and epsilon contract
    time_neg: Dict[str, Any] = {
        "eir_unit": time_cfg.get("unit", "us"),
        "device_resolution_ns": time_resolution_ns,
        "resolution_us": res_us,
        "mode": mode,
    }
    if mode == "fixed_step":
        if dt_us_req is None or not isinstance(dt_us_req, int) or dt_us_req < 1:
            raise ValueError("backend.time_config_invalid: fixed_step requires positive fixed_step_dt_us")
        # Quantize to nearest multiple of device resolution (in microseconds)
        q = round(dt_us_req / res_us) if res_us > 0 else dt_us_req
        if q < 1:
            q = 1
        dt_us_sel = q * res_us
        quant_err = abs(dt_us_sel - dt_us_req)
        time_neg.update(
            {
                "dt_us_requested": dt_us_req,
                "dt_us_selected": int(round(dt_us_sel)),
                "quantization_error_us": quant_err,
                "meets_epsilon": quant_err <= eps_time_us,
            }
        )
        if quant_err > eps_time_us:
            raise ValueError("backend.time_quantization_violation: fixed_step dt cannot meet epsilon_time_us")
        dt_us_final = int(round(dt_us_sel))
    else:
        # exact_event: worst-case quantization if device schedules on discrete ticks
        worst_case = res_us / 2.0
        time_neg.update({"worst_case_quantization_us": worst_case, "meets_epsilon": worst_case <= eps_time_us})
        if worst_case > eps_time_us:
            raise ValueError("backend.time_quantization_violation: exact_event cannot meet epsilon_time_us with device resolution")
        dt_us_final = None

    negotiation["time"] = time_neg

    # Overflow policy negotiation (substitute if mismatch)
    requested_policy = (eir.get("security", {}) or {}).get("overflow_policy")
    device_policy = dcd.get("overflow_behavior")
    pol = {"requested": requested_policy, "device": device_policy}
    if requested_policy and device_policy and requested_policy != device_policy:
        warnings.append(f"overflow policy '{requested_policy}' not supported; substituting '{device_policy}'")
        pol["action"] = "substitute"
    else:
        pol["action"] = "match"
    negotiation["policies"] = pol

    # Operator support; mark unsupported as emulated
    emulated_nodes: List[Dict[str, Any]] = []
    total_nodes = 0
    for n in (eir.get("nodes", []) or []):
        total_nodes += 1
        kind = n.get("kind")
        op = n.get("op")
        if kind in ("spiking_neuron", "synapse", "kernel") and op:
            if op not in supported_ops:
                emulated_nodes.append({"id": n.get("id"), "kind": kind, "op": op})
    negotiation["ops"] = {
        "total_nodes": total_nodes,
        "unsupported_ops": sorted({x["op"] for x in emulated_nodes}),
        "emulated_count": len(emulated_nodes),
    }

    any_emulated = (len(emulated_nodes) > 0) or (mode not in deterministic_modes) or (mode == "exact_event" and fixed_only)

    plan = {
        "backend": {"name": "cpu-sim", "version": dcd.get("version", "0.1.0"), "mode": mode},
        "graph": {
            "id": eir.get("graph", {}).get("name", "graph"),
            "profile": eir.get("profile"),
            "seed": eir.get("seed", 0),
        },
        "partitions": [
            {
                "id": "p0",
                "nodes": [n.get("id") for n in eir.get("nodes", [])],
                "placement": {"chip": 0, "core": 0},
                "resources": {},
                "emulated": any_emulated,
            }
        ],
        "schedule": [
            {
                "partition_id": "p0",
                "policy": ("fixed" if mode == "fixed_step" else "event"),
                "dt_us": dt_us_final,
                "priority": 0,
                "affinity": 0,
            }
        ],
        "probes": eir.get("probes", []),
        "epsilons": {"time_us": eps_time_us, "numeric": eps_numeric},
        "warnings": warnings,
        "capabilities": {
            "device": {"name": dcd.get("name"), "version": dcd.get("version")},
            "supported_ops": sorted(list(supported_ops)),
            "deterministic_modes": sorted(list(deterministic_modes)),
            "conformance_profiles": sorted(list(profiles)),
            "emulated_nodes": emulated_nodes,
        },
        "negotiation": negotiation,
        "notes": "cpu-sim plan (deterministic executor with capability negotiation)",
    }
    return plan


def run_cpu_sim(plan: Dict[str, Any], inputs: List[str], out_trace_path: str) -> Dict[str, Any]:
    # Read inputs (Event Tensor JSONL), collect records
    records: List[Tuple[int, List[int], float]] = []
    dims: List[str] = []
    units_value = "dimensionless"
    seed = plan.get("graph", {}).get("seed", 0)

    # Choose dims/units from the first input header
    header_loaded = False

    for path in inputs:
        with open(path, "r", encoding="utf-8") as f:
            line0 = f.readline()
            if not line0:
                continue
            header_obj = json.loads(line0)
            header = header_obj.get("header", {})
            if not header_loaded:
                dims = header.get("dims", []) or ["x", "y", "polarity"]
                units = header.get("units", {})
                units_value = units.get("value", "dimensionless")
                header_loaded = True
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                ts = int(rec["ts"])
                idx = list(rec["idx"])
                val = float(rec.get("val", 1.0))
                records.append((ts, idx, val))

    # Sort deterministically
    records.sort(key=_canonical_key)

    # Emit golden trace
    os.makedirs(os.path.dirname(out_trace_path) or ".", exist_ok=True)
    with open(out_trace_path, "w", encoding="utf-8") as out:
        meta = {
            "backend": "cpu-sim",
            "plan_mode": plan.get("backend", {}).get("mode"),
            "graph": plan.get("graph", {}).get("id"),
            "seed": seed,
        }
        _write_header(out, dims=dims or ["x", "y", "polarity"], units_value=units_value, meta=meta)
        for ts, idx, val in records:
            _write_rec(out, ts, idx, val)

    return {
        "status": "ok",
        "trace_path": out_trace_path,
        "count": len(records),
    }
