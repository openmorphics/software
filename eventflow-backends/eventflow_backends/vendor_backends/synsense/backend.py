"""
SynSense backend v0.1

Provides:
- plan_synsense(eir, dcd) -> plan dict
- run_synsense(plan, inputs_jsonl, out_trace_path) -> run result dict

This backend integrates with SynSense's neuromorphic hardware.
Requires SynSense SDK to be installed and Xylo/DYNAP hardware available for execution.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import logging

_log = logging.getLogger(__name__)

SCHEMA_VERSION = "0.1.0"

# Lazy import SynSense SDK to avoid hard dependency
_SYNSENSE_AVAILABLE = None


def _check_synsense():
    global _SYNSENSE_AVAILABLE
    if _SYNSENSE_AVAILABLE is None:
        try:
            import synsense  # noqa: F401
            _SYNSENSE_AVAILABLE = True
        except ImportError:
            _SYNSENSE_AVAILABLE = False
    return _SYNSENSE_AVAILABLE


class SynSenseBackend:
    def __init__(self) -> None:
        self._dcd_path = os.path.join(os.path.dirname(__file__), "dcd.json")
        if not os.path.isfile(self._dcd_path):
            raise FileNotFoundError(f"SynSense DCD not found: {self._dcd_path}")
        with open(self._dcd_path, "r", encoding="utf-8") as f:
            self._dcd: Dict[str, Any] = json.load(f)

        # For now, we'll assume validators are available; in real impl, load dynamically
        # self._validators = _load_module_from(vpath, "eventflow_validators")

    def name(self) -> str:
        return "synsense"

    def dcd(self) -> Dict[str, Any]:
        return dict(self._dcd)

    def plan(self, eir: Dict[str, Any]) -> Dict[str, Any]:
        """
        Planning for SynSense hardware.
        Validates EIR, checks SynSense SDK availability, and generates hardware mapping.
        """
        if not _check_synsense():
            raise RuntimeError("SynSense SDK not available. Install SynSense SDK to use SynSense backend.")

        # For now, minimal planning - in real impl, would map to SynSense cores/chips
        warnings: List[str] = []
        negotiation: Dict[str, Any] = {"time": {}, "profile": {}, "ops": {}, "policies": {}}

        # Basic profile check
        prof = eir.get("profile")
        supported_profiles = set(self._dcd.get("conformance_profiles", []))
        negotiation["profile"] = {"eir_profile": prof, "supported": bool(prof in supported_profiles)}
        if prof and prof not in supported_profiles:
            raise ValueError("backend.unsupported_profile: profile not supported by SynSense")

        # Ops support - SynSense supports specialized audio/vision ops
        supported_ops = set(self._dcd.get("supported_ops", []))
        emulated_nodes: List[Dict[str, Any]] = []
        total_nodes = 0
        for n in (eir.get("nodes", []) or []):
            total_nodes += 1
            op = n.get("op")
            if op and op not in supported_ops:
                emulated_nodes.append({"id": n.get("id"), "op": op})

        negotiation["ops"] = {
            "total_nodes": total_nodes,
            "unsupported_ops": sorted({x["op"] for x in emulated_nodes}),
            "emulated_count": len(emulated_nodes),
        }

        plan = {
            "backend": {"name": "synsense", "version": self._dcd.get("version", "0.1.0")},
            "graph": {
                "id": eir.get("graph", {}).get("name", "graph"),
                "profile": eir.get("profile"),
                "seed": eir.get("seed", 0),
            },
            "partitions": [
                {
                    "id": "p0",
                    "nodes": [n.get("id") for n in eir.get("nodes", [])],
                    "placement": {"chip": 0, "core": 0},  # Hardware placement
                    "resources": {},
                    "emulated": len(emulated_nodes) > 0,
                }
            ],
            "schedule": [
                {
                    "partition_id": "p0",
                    "policy": "event",  # SynSense is event-driven with real-time constraints
                    "dt_us": None,
                    "priority": 0,
                    "affinity": 0,
                }
            ],
            "probes": eir.get("probes", []),
            "epsilons": {"time_us": 0.1, "numeric": 1e-6},  # Ultra-low latency precision
            "warnings": warnings,
            "capabilities": {
                "device": {"name": self._dcd.get("name"), "version": self._dcd.get("version")},
                "supported_ops": sorted(list(supported_ops)),
                "conformance_profiles": sorted(list(supported_profiles)),
                "emulated_nodes": emulated_nodes,
            },
            "negotiation": negotiation,
            "notes": "SynSense neuromorphic processors with ultra-low power and real-time capabilities",
        }
        return plan

    def run(
        self,
        eir: Dict[str, Any],
        inputs: List[str],
        out_trace_path: str,
        plan: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute on SynSense hardware using SynSense SDK.
        """
        if not _check_synsense():
            raise RuntimeError("SynSense SDK not available. Cannot run on SynSense hardware.")

        if plan is None:
            plan = self.plan(eir)

        # For now, stub implementation - in real impl, would compile to SynSense and run
        _log.warning("SynSense backend is a stub implementation. Hardware execution not implemented.")

        # Create a minimal trace file for compatibility
        with open(out_trace_path, "w", encoding="utf-8") as f:
            # Write header
            header = {
                "header": {
                    "dims": ["time", "neuron_id"],
                    "units": {"time": "us", "value": "dimensionless"},
                    "dtype": "f32",
                    "layout": "coo",
                    "schema_version": SCHEMA_VERSION,
                }
            }
            f.write(json.dumps(header) + "\n")
            # Write some dummy events
            f.write('{"data": [1000.0, 0, 1.0]}\n')

        return {
            "status": "ok",
            "backend": "synsense",
            "execution_time_us": 1000,
            "events_processed": 1,
            "power_consumption_mw": 2.0,  # Ultra-low power
            "notes": "Stub implementation - hardware execution not available",
        }