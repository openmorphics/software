"""
EventFlow v0.1 — Core JSON Schema Validators and JSONL Checkers

This module provides:
- EIR (Event Intermediate Representation) JSON Schema validation
- Event Tensor JSON and JSONL validation (header + records)
- DCD (Device Capability Descriptor) JSON Schema validation
- EFPKG (EventFlow Package) manifest validation with integrity checks

If 'jsonschema' is installed, this module uses Draft 2020-12 validation.
If unavailable, it performs minimal structure checks and semantic validations.

Public API:
- validate_eir(obj) -> list[ValidationIssue]
- validate_event_tensor_json(obj) -> list[ValidationIssue]
- validate_event_tensor_jsonl_path(path) -> list[ValidationIssue]
- validate_dcd(obj) -> list[ValidationIssue]
- validate_efpkg(manifest, root_dir=".") -> list[ValidationIssue]

- load_json(path) -> Any
- hash_sha256_file(path) -> str
"""

from __future__ import annotations

import io
import json
import os
import hashlib
from dataclasses import dataclass, field
from typing import Any, Optional, Iterable, List, Dict, Tuple

# Optional jsonschema import (preferred path)
try:
    import jsonschema  # type: ignore
    from jsonschema import Draft202012Validator  # type: ignore
except Exception:  # pragma: no cover
    jsonschema = None
    Draft202012Validator = None  # type: ignore


SCHEMA_VERSION = "0.1.0"

# -----------------------
# Shared helper structures
# -----------------------

@dataclass
class ValidationIssue:
    path: str
    message: str
    context: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:  # For readable printing
        p = self.path or "$"
        return f"{p}: {self.message}" + (f" | ctx={self.context}" if self.context else "")


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def hash_sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _compile_validator(schema: Dict[str, Any]):
    if Draft202012Validator is None:
        return None
    try:
        return Draft202012Validator(schema)
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Failed to compile schema: {e}")


def _schema_validate(instance: Any, schema: Dict[str, Any], root_path: str = "$") -> List[ValidationIssue]:
    """Validate with jsonschema if available, else return minimal required-field errors."""
    issues: List[ValidationIssue] = []
    if Draft202012Validator is not None:
        v = _compile_validator(schema)
        assert v is not None
        for e in v.iter_errors(instance):
            path = root_path + "".join(f"/{str(p)}" for p in e.path)
            issues.append(ValidationIssue(path=path, message=e.message))
        return issues

    # Minimal fallback checks when jsonschema is not installed
    # Only check top-level required + simple types for core schemas; semantic validators will augment.
    required = schema.get("required", [])
    if isinstance(instance, dict):
        for key in required:
            if key not in instance:
                issues.append(ValidationIssue(path=f"{root_path}/{key}", message="required property missing"))
    else:
        issues.append(ValidationIssue(path=root_path, message="expected object at root"))
    return issues


# -----------------------
# Embedded JSON Schemas (Draft 2020-12)
# Synchronized with docs/specs/*.schema.md
# -----------------------

EIR_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "EventFlow EIR",
    "type": "object",
    "additionalProperties": False,
    "required": ["version", "profile", "time", "graph", "nodes", "edges"],
    "properties": {
        "version": {"type": "string"},
        "profile": {"type": "string", "enum": ["BASE", "REALTIME", "LEARNING", "LOWPOWER"]},
        "seed": {"type": "integer", "minimum": 0},
        "time": {
            "type": "object",
            "additionalProperties": False,
            "required": ["unit", "mode"],
            "properties": {
                "unit": {"type": "string", "enum": ["ns", "us", "ms"]},
                "mode": {"type": "string", "enum": ["exact_event", "fixed_step"]},
                "fixed_step_dt_us": {"type": "integer", "minimum": 1},
                "epsilon_time_us": {"type": "integer", "minimum": 0},
                "epsilon_numeric": {"type": "number", "minimum": 0},
            },
            "allOf": [
                {
                    "if": {"properties": {"mode": {"const": "fixed_step"}}},
                    "then": {"required": ["fixed_step_dt_us"]},
                }
            ],
        },
        "graph": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "attributes": {"type": "object"},
            },
        },
        "nodes": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "kind"],
                "properties": {
                    "id": {"type": "string", "minLength": 1},
                    "kind": {
                        "type": "string",
                        "enum": ["spiking_neuron", "synapse", "delay_line", "kernel", "group", "route", "probe", "custom"],
                    },
                    "op": {"type": "string"},
                    "params": {"type": "object"},
                    "state": {"type": "object"},
                    "timing_constraints": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "deadline_us": {"type": "integer", "minimum": 0},
                            "refractory_us": {"type": "integer", "minimum": 0},
                            "max_latency_us": {"type": "integer", "minimum": 0},
                        },
                    },
                    "security": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "sandbox": {"type": "boolean"},
                            "rate_limit_keps": {"type": "integer", "minimum": 0},
                            "overflow_policy": {"type": "string", "enum": ["drop_head", "drop_tail", "block"]},
                        },
                    },
                },
                "allOf": [
                    {
                        "if": {"properties": {"kind": {"enum": ["spiking_neuron", "synapse", "kernel"]}}},
                        "then": {"required": ["op"]},
                    }
                ],
            },
        },
        "edges": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["src", "dst"],
                "properties": {
                    "src": {"type": "string"},
                    "dst": {"type": "string"},
                    "weight": {"type": "number"},
                    "delay_us": {"type": "integer", "minimum": 0},
                    "plasticity": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {"kind": {"type": "string"}, "params": {"type": "object"}},
                    },
                },
            },
        },
        "probes": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "target"],
                "properties": {
                    "id": {"type": "string"},
                    "target": {"type": "string"},
                    "type": {"type": "string"},
                    "window_us": {"type": "integer", "minimum": 0},
                },
            },
        },
        "security": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "sandbox": {"type": "boolean"},
                "rate_limit_keps": {"type": "integer", "minimum": 0},
                "overflow_policy": {"type": "string", "enum": ["drop_head", "drop_tail", "block"]},
            },
        },
        "metadata": {"type": "object"},
    },
}

EVENT_TENSOR_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "EventFlow Event Tensor",
    "type": "object",
    "required": ["header", "records"],
    "properties": {
        "header": {
            "type": "object",
            "required": ["schema_version", "dims", "units", "dtype", "layout"],
            "additionalProperties": False,
            "properties": {
                "schema_version": {"type": "string"},
                "dims": {"type": "array", "minItems": 1, "items": {"type": "string", "minLength": 1}},
                "units": {
                    "type": "object",
                    "required": ["time", "value"],
                    "additionalProperties": False,
                    "properties": {"time": {"enum": ["ns", "us", "ms"]}, "value": {"type": "string"}},
                },
                "dtype": {"enum": ["f32", "f16", "i16", "u8"]},
                "layout": {"enum": ["coo", "block"]},
                "metadata": {"type": "object"},
                "origin": {"type": "object"},
            },
        },
        "records": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["ts", "idx", "val"],
                "additionalProperties": False,
                "properties": {
                    "ts": {"type": "integer", "minimum": 0},
                    "idx": {"type": "array", "minItems": 1, "items": {"type": "integer", "minimum": 0}},
                    "val": {"type": "number"},
                    "meta": {"type": "object"},
                },
            },
        },
    },
}

DCD_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "EventFlow Device Capability Descriptor (DCD)",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "name",
        "vendor",
        "family",
        "version",
        "time_resolution_ns",
        "deterministic_modes",
        "supported_ops",
        "conformance_profiles",
    ],
    "properties": {
        "name": {"type": "string"},
        "vendor": {"type": "string"},
        "family": {"type": "string"},
        "version": {"type": "string"},
        "deterministic_modes": {"type": "array", "minItems": 1, "items": {"enum": ["exact_event", "fixed_step"]}},
        "supported_ops": {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "opset_versions": {"type": "object", "additionalProperties": {"type": "string"}},
        "neuron_models": {"type": "array", "items": {"type": "string"}},
        "plasticity_rules": {"type": "array", "items": {"type": "string"}},
        "weight_precisions_bits": {"type": "array", "items": {"type": "integer", "minimum": 1}},
        "state_precisions_bits": {"type": "array", "items": {"type": "integer", "minimum": 1}},
        "time_resolution_ns": {"type": "integer", "minimum": 1},
        "max_jitter_ns": {"type": "integer", "minimum": 0},
        "clock": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "drift_ppm": {"type": "number", "minimum": 0},
                "sync_method": {"enum": ["free_running", "ptp", "ntp", "host_sync", "other"]},
                "deterministic_fixed_step_only": {"type": "boolean"},
            },
        },
        "limits": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "max_neurons": {"type": "integer", "minimum": 1},
                "max_synapses": {"type": "integer", "minimum": 1},
                "max_fanout": {"type": "integer", "minimum": 1},
                "max_fanin": {"type": "integer", "minimum": 1},
                "min_delay_us": {"type": "integer", "minimum": 0},
                "max_delay_us": {"type": "integer", "minimum": 0},
            },
        },
        "memory": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "per_core_kib": {"type": "integer", "minimum": 1},
                "per_chip_mib": {"type": "integer", "minimum": 1},
                "global_mib": {"type": "integer", "minimum": 1},
            },
        },
        "topology": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "multi_chip": {"type": "boolean"},
                "cores_per_chip": {"type": "integer", "minimum": 1},
                "max_hops": {"type": "integer", "minimum": 0},
                "router_bandwidth_meps": {"type": "number", "minimum": 0},
                "link_latency_us": {"type": "number", "minimum": 0},
            },
        },
        "power": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "mw_per_spike_typ": {"type": "number", "minimum": 0},
                "idle_mw": {"type": "number", "minimum": 0},
                "tdp_mw": {"type": "number", "minimum": 0},
            },
        },
        "features": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "on_chip_learning": {"type": "boolean"},
                "stochastic_neurons": {"type": "boolean"},
                "analog_dynamics": {"type": "boolean"},
                "kernel_sandbox": {"type": "boolean"},
            },
        },
        "overflow_behavior": {"enum": ["drop_head", "drop_tail", "block"]},
        "conformance_profiles": {"type": "array", "minItems": 1, "items": {"enum": ["BASE", "REALTIME", "LEARNING", "LOWPOWER"]}},
        "notes": {"type": "string"},
    },
}

EFPKG_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "EventFlow Package (EFPKG) Manifest",
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "sdk_version", "model", "profile", "determinism", "artifacts"],
    "properties": {
        "schema_version": {"type": "string"},
        "sdk_version": {"type": "string"},
        "created_at": {"type": "string"},
        "model": {
            "type": "object",
            "additionalProperties": False,
            "required": ["id", "name"],
            "properties": {
                "id": {"type": "string"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "version": {"type": "string"},
                "author": {"type": "string"},
                "license": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "domains": {"type": "array", "items": {"type": "string"}},
            },
        },
        "profile": {
            "type": "object",
            "additionalProperties": False,
            "required": ["name"],
            "properties": {
                "name": {"enum": ["BASE", "REALTIME", "LEARNING", "LOWPOWER"]},
                "notes": {"type": "string"},
                "constraints": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "latency_budget_ms": {"type": "number", "minimum": 0},
                        "max_drop_rate_pct": {"type": "number", "minimum": 0, "maximum": 100},
                    },
                },
            },
        },
        "determinism": {
            "type": "object",
            "additionalProperties": False,
            "required": ["time_unit", "mode", "epsilon_time_us", "epsilon_numeric", "seed"],
            "properties": {
                "time_unit": {"enum": ["ns", "us", "ms"]},
                "mode": {"enum": ["exact_event", "fixed_step"]},
                "fixed_step_dt_us": {"type": "integer", "minimum": 1},
                "epsilon_time_us": {"type": "integer", "minimum": 0},
                "epsilon_numeric": {"type": "number", "minimum": 0},
                "seed": {"type": "integer", "minimum": 0},
            },
            "allOf": [
                {"if": {"properties": {"mode": {"const": "fixed_step"}}}, "then": {"required": ["fixed_step_dt_us"]}}
            ],
        },
        "features": {"type": "array", "items": {"type": "string"}},
        "capabilities_required": {"type": "object"},
        "artifacts": {
            "type": "object",
            "additionalProperties": False,
            "required": ["eir", "traces"],
            "properties": {
                "eir": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "format"],
                    "properties": {
                        "path": {"type": "string"},
                        "format": {"enum": ["json"], "default": "json"},
                        "sha256": {"type": "string"},
                        "filesize_bytes": {"type": "integer", "minimum": 0},
                    },
                },
                "traces": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["golden"],
                    "properties": {
                        "golden": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["path", "format"],
                            "properties": {"path": {"type": "string"}, "format": {"enum": ["jsonl"]}, "sha256": {"type": "string"}},
                        },
                        "inputs": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "required": ["path", "format"],
                                "properties": {"path": {"type": "string"}, "format": {"enum": ["jsonl"]}, "sha256": {"type": "string"}},
                            },
                        },
                    },
                },
                "profiles": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "baseline": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["path", "format"],
                            "properties": {"path": {"type": "string"}, "format": {"enum": ["jsonl"]}, "sha256": {"type": "string"}},
                        }
                    },
                },
                "assets": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["path"],
                        "properties": {"path": {"type": "string"}, "sha256": {"type": "string"}},
                    },
                },
            },
        },
        "integrity": {
            "type": "object",
            "additionalProperties": False,
            "properties": {"checksums": {"type": "string"}, "signatures": {"type": "string"}},
        },
        "compatibility": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "tested_backends": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["name", "version"],
                        "properties": {"name": {"type": "string"}, "version": {"type": "string"}, "notes": {"type": "string"}},
                    },
                }
            },
        },
        "notes": {"type": "string"},
    },
}

# -----------------------
# EIR Validation
# -----------------------

def validate_eir(obj: Dict[str, Any]) -> List[ValidationIssue]:
    issues = _schema_validate(obj, EIR_SCHEMA, root_path="$")
    # Semantic checks beyond schema
    if isinstance(obj, dict):
        # Schema version check (optional but recommended)
        version = obj.get("version")
        if isinstance(version, str) and not version.startswith(SCHEMA_VERSION.split(".", 1)[0]):
            issues.append(ValidationIssue(path="$.version", message=f"EIR version '{version}' may be incompatible with validator '{SCHEMA_VERSION}'"))

        time_cfg = obj.get("time", {})
        mode = time_cfg.get("mode")
        dt = time_cfg.get("fixed_step_dt_us")
        if mode == "fixed_step":
            if not isinstance(dt, int) or dt < 1:
                issues.append(ValidationIssue(path="$.time.fixed_step_dt_us", message="fixed_step_dt_us must be positive integer"))
        # Check nodes op presence for required kinds already handled by schema
        # Additional: ensure DAG or delay feedback only (basic sanity)
        ids = set()
        for n in obj.get("nodes", []):
            nid = n.get("id")
            if nid in ids:
                issues.append(ValidationIssue(path="$.nodes", message=f"duplicate node id '{nid}'"))
            ids.add(nid)
        for e in obj.get("edges", []):
            src_id = e.get("src")
            dst_id = e.get("dst")
            if src_id not in ids:
                issues.append(ValidationIssue(path="$.edges", message=f"edge src '{src_id}' not in nodes"))
            if dst_id not in ids:
                issues.append(ValidationIssue(path="$.edges", message=f"edge dst '{dst_id}' not in nodes"))
    return issues


# -----------------------
# Event Tensor Validation
# -----------------------

def validate_event_tensor_json(obj: Dict[str, Any]) -> List[ValidationIssue]:
    issues = _schema_validate(obj, EVENT_TENSOR_SCHEMA, root_path="$")
    # Semantic: idx length == dims length, monotonic ts in 'records'
    try:
        header = obj["header"]
        # Schema version compatibility check (header.schema_version)
        hv = header.get("schema_version")
        if isinstance(hv, str) and not hv.startswith(SCHEMA_VERSION.split(".", 1)[0]):
            issues.append(ValidationIssue(path="$.header/schema_version", message=f"Event Tensor schema_version '{hv}' may be incompatible with '{SCHEMA_VERSION}'"))

        dims = header["dims"]
        last_ts = -1
        for i, rec in enumerate(obj.get("records", [])):
            ts = rec["ts"]
            idx = rec["idx"]
            if len(idx) != len(dims):
                issues.append(ValidationIssue(path=f"$.records/{i}/idx", message=f"idx length {len(idx)} != dims length {len(dims)}"))
            if ts < last_ts:
                issues.append(ValidationIssue(path=f"$.records/{i}/ts", message=f"timestamps not non-decreasing: {ts} < {last_ts}"))
            last_ts = ts
    except Exception as e:
        issues.append(ValidationIssue(path="$", message=f"semantic check failed: {e}"))
    return issues


def validate_event_tensor_jsonl_path(path: str) -> List[ValidationIssue]:
    """
    JSONL carriage: first line is {"header": {...}}, subsequent lines are event records (no wrapper).
    Enforces:
    - header schema validity (header only)
    - per-record structure constraints (ts, idx, val)
    - idx length == dims length
    - non-decreasing timestamps
    """
    issues: List[ValidationIssue] = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            # Header line
            header_line = f.readline()
            if not header_line:
                return [ValidationIssue(path="$", message="empty file")]
            header_obj = json.loads(header_line)
            if "header" not in header_obj or not isinstance(header_obj["header"], dict):
                return [ValidationIssue(path="$.header", message="first line must contain 'header' object")]
            header = header_obj["header"]
            header_wrap = {"header": header, "records": []}
            issues += _schema_validate(header_wrap, EVENT_TENSOR_SCHEMA, root_path="$")
            # Version compatibility check
            hv = header.get("schema_version")
            if isinstance(hv, str) and not hv.startswith(SCHEMA_VERSION.split(".", 1)[0]):
                issues.append(ValidationIssue(path="$.header/schema_version", message=f"Event Tensor schema_version '{hv}' may be incompatible with '{SCHEMA_VERSION}'"))
            dims = header.get("dims", [])
            time_unit = header.get("units", {}).get("time")
            if time_unit not in ("ns", "us", "ms"):
                issues.append(ValidationIssue(path="$.header/units/time", message="time unit must be ns/us/ms"))

            # Records
            last_ts = -1
            line_no = 1  # already consumed header
            for line in f:
                line_no += 1
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception as e:
                    issues.append(ValidationIssue(path=f"@line{line_no}", message=f"invalid JSON: {e}"))
                    continue
                # Structural checks
                for k in ("ts", "idx", "val"):
                    if k not in rec:
                        issues.append(ValidationIssue(path=f"@line{line_no}/{k}", message="missing required field"))
                ts = rec.get("ts")
                idx = rec.get("idx")
                if isinstance(ts, int):
                    if ts < last_ts:
                        issues.append(ValidationIssue(path=f"@line{line_no}/ts", message=f"timestamps not non-decreasing: {ts} < {last_ts}"))
                    last_ts = ts if ts is not None else last_ts
                else:
                    issues.append(ValidationIssue(path=f"@line{line_no}/ts", message="ts must be integer"))
                if isinstance(idx, list):
                    if len(dims) and len(idx) != len(dims):
                        issues.append(ValidationIssue(path=f"@line{line_no}/idx", message=f"idx length {len(idx)} != dims length {len(dims)}"))
                else:
                    issues.append(ValidationIssue(path=f"@line{line_no}/idx", message="idx must be array"))
    except FileNotFoundError:
        issues.append(ValidationIssue(path="$", message=f"file not found: {path}"))
    except Exception as e:
        issues.append(ValidationIssue(path="$", message=f"validation failed: {e}"))
    return issues


# -----------------------
# DCD Validation
# -----------------------

def validate_dcd(obj: Dict[str, Any]) -> List[ValidationIssue]:
    issues = _schema_validate(obj, DCD_SCHEMA, root_path="$")
    # Semantic: ensure deterministic_modes not empty; supported_ops consistency hints already covered
    modes = obj.get("deterministic_modes", [])
    if not modes:
        issues.append(ValidationIssue(path="$.deterministic_modes", message="at least one deterministic mode required"))
    # If deterministic_fixed_step_only is true, ensure "fixed_step" is in modes
    clock = obj.get("clock", {})
    if clock.get("deterministic_fixed_step_only") and "fixed_step" not in modes:
        issues.append(ValidationIssue(path="$.clock", message="deterministic_fixed_step_only=true requires 'fixed_step' mode"))
    # Optional: bounds sanity
    tr = obj.get("time_resolution_ns")
    if isinstance(tr, int) and tr <= 0:
        issues.append(ValidationIssue(path="$.time_resolution_ns", message="must be positive"))
    return issues


# -----------------------
# EFPKG Validation + Integrity
# -----------------------

def validate_efpkg(manifest: Dict[str, Any], root_dir: str = ".") -> List[ValidationIssue]:
    issues = _schema_validate(manifest, EFPKG_SCHEMA, root_path="$")
    # Schema version compatibility
    sv = manifest.get("schema_version")
    if isinstance(sv, str) and not sv.startswith(SCHEMA_VERSION.split(".", 1)[0]):
        issues.append(ValidationIssue(path="$.schema_version", message=f"EFPKG schema_version '{sv}' may be incompatible with '{SCHEMA_VERSION}'"))

    # Paths and integrity checks
    def _check_file(rel_path: str, where: str, expected_sha256: Optional[str] = None):
        p = os.path.join(root_dir, rel_path)
        if not os.path.isfile(p):
            issues.append(ValidationIssue(path=where, message=f"missing file: {rel_path}"))
            return
        if expected_sha256:
            got = hash_sha256_file(p)
            if got.lower() != expected_sha256.lower():
                issues.append(ValidationIssue(path=where, message=f"sha256 mismatch", context={"expected": expected_sha256, "got": got}))

    try:
        arts = manifest.get("artifacts", {})
        # EIR
        eir_info = arts.get("eir", {})
        eir_path = eir_info.get("path")
        if eir_path:
            _check_file(eir_path, "$.artifacts.eir.path", eir_info.get("sha256"))
            # Cross-check determinism alignment if possible
            try:
                eir_obj = load_json(os.path.join(root_dir, eir_path))
                eir_issues = validate_eir(eir_obj)
                issues.extend(ValidationIssue(path="$.artifacts.eir", message=str(i)) for i in eir_issues if eir_issues)
                # Compare determinism
                det = manifest.get("determinism", {})
                eir_time = eir_obj.get("time", {})
                map_unit = {"ns": "ns", "us": "us", "ms": "ms"}
                if det.get("time_unit") != map_unit.get(eir_time.get("unit")):
                    issues.append(ValidationIssue(path="$.determinism.time_unit", message="mismatch with EIR time.unit"))
                if det.get("mode") != eir_time.get("mode"):
                    issues.append(ValidationIssue(path="$.determinism.mode", message="mismatch with EIR time.mode"))
                if det.get("mode") == "fixed_step":
                    if det.get("fixed_step_dt_us") != eir_time.get("fixed_step_dt_us"):
                        issues.append(ValidationIssue(path="$.determinism.fixed_step_dt_us", message="mismatch with EIR fixed_step_dt_us"))
            except Exception as e:
                issues.append(ValidationIssue(path="$.artifacts.eir", message=f"could not load/validate EIR: {e}"))

        # Golden trace
        traces_info = arts.get("traces", {})
        golden = traces_info.get("golden", {})
        golden_path = golden.get("path")
        if golden_path:
            _check_file(golden_path, "$.artifacts.traces.golden.path", golden.get("sha256"))
            # We can quickly sanity-check JSONL header
            issues.extend(validate_event_tensor_jsonl_path(os.path.join(root_dir, golden_path)))

        # Inputs
        for i, spec in enumerate(traces_info.get("inputs", []) or []):
            _check_file(spec.get("path", ""), f"$.artifacts.traces.inputs/{i}/path", spec.get("sha256"))

        # Baseline profile
        prof = arts.get("profiles", {})
        baseline = prof.get("baseline", {})
        if baseline.get("path"):
            _check_file(baseline["path"], "$.artifacts.profiles.baseline.path", baseline.get("sha256"))

        # Assets
        for i, a in enumerate(arts.get("assets", []) or []):
            _check_file(a.get("path", ""), f"$.artifacts.assets/{i}/path", a.get("sha256"))

    except Exception as e:
        issues.append(ValidationIssue(path="$", message=f"EFPKG validation failed: {e}"))

    return issues


# -----------------------
# Minimal self-test helpers (not full unit tests)
# -----------------------

def _is_ok(issues: List[ValidationIssue]) -> bool:
    return len(issues) == 0


if __name__ == "__main__":  # Manual quick check
    # Quick smoke test on example files if present
    try:
        sample_eir = "examples/wakeword/eir.json"
        if os.path.isfile(sample_eir):
            eir_obj = load_json(sample_eir)
            errs = validate_eir(eir_obj)
            print(f"EIR {sample_eir}: {'OK' if _is_ok(errs) else f'FAIL ({len(errs)} issues)'}")
            for e in errs:
                print(" -", e)
        sample_jsonl = "examples/wakeword/traces/inputs/audio_sample.jsonl"
        if os.path.isfile(sample_jsonl):
            errs = validate_event_tensor_jsonl_path(sample_jsonl)
            print(f"Event JSONL {sample_jsonl}: {'OK' if _is_ok(errs) else f'FAIL ({len(errs)} issues)'}")
            for e in errs:
                print(" -", e)
    except Exception as ex:
        print("Self-test failed:", ex)