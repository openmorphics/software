"""
SpiNNaker backend v0.1

Provides:
- plan_spinnaker(eir, dcd) -> plan dict
- run_spinnaker(plan, inputs_jsonl, out_trace_path) -> run result dict

This backend integrates with SpiNNaker neuromorphic hardware.
Requires sPyNNaker to be installed and SpiNNaker hardware available for execution.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

import logging

_log = logging.getLogger(__name__)

SCHEMA_VERSION = "0.1.0"

# Lazy import sPyNNaker to avoid hard dependency
_SPYNNAKER_AVAILABLE = None


def _check_spynnaker():
    global _SPYNNAKER_AVAILABLE
    if _SPYNNAKER_AVAILABLE is None:
        try:
            import spynnaker8 as sim  # noqa: F401
            _SPYNNAKER_AVAILABLE = True
        except ImportError:
            _SPYNNAKER_AVAILABLE = False
    return _SPYNNAKER_AVAILABLE


class SpiNNakerBackend:
    def __init__(self) -> None:
        self._dcd_path = os.path.join(os.path.dirname(__file__), "dcd.json")
        if not os.path.isfile(self._dcd_path):
            raise FileNotFoundError(f"SpiNNaker DCD not found: {self._dcd_path}")
        with open(self._dcd_path, "r", encoding="utf-8") as f:
            self._dcd: Dict[str, Any] = json.load(f)

        # Load validators (reuse from cpu_sim for now)
        vpath = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "eventflow-core", "validators.py")
        vpath = os.path.abspath(vpath)
        # For now, we'll assume validators are available; in real impl, load dynamically
        # self._validators = _load_module_from(vpath, "eventflow_validators")

    def name(self) -> str:
        return "spinnaker"

    def dcd(self) -> Dict[str, Any]:
        return dict(self._dcd)

    def _validate_eir(self, eir: Dict[str, Any]) -> tuple[str, Dict[str, Any], List[Dict[str, Any]]]:
        if not isinstance(eir, dict):
            raise TypeError("EIR must be a dictionary")

        if "profile" not in eir:
            raise KeyError("profile")
        prof = eir.get("profile")
        if not isinstance(prof, str):
            raise TypeError("profile must be a string")

        supported_profiles = set(self._dcd.get("conformance_profiles", []))
        if prof not in supported_profiles:
            raise ValueError("backend.unsupported_profile: profile not supported by SpiNNaker")

        graph = eir.get("graph")
        if not isinstance(graph, dict):
            raise KeyError("graph")

        nodes = eir.get("nodes", []) or []
        if not isinstance(nodes, list):
            raise TypeError("nodes must be a list")

        return prof, graph, nodes

    def plan(self, eir: Dict[str, Any]) -> Dict[str, Any]:
        """
        Planning for SpiNNaker hardware.
        Validates EIR, checks sPyNNaker availability, and generates hardware mapping.
        """
        prof, graph, nodes = self._validate_eir(eir)

        if not _check_spynnaker():
            raise RuntimeError("sPyNNaker not available. Install sPyNNaker to use SpiNNaker backend.")

        # For now, minimal planning - in real impl, would map to SpiNNaker chips/cores
        warnings: List[str] = []
        negotiation: Dict[str, Any] = {"time": {}, "profile": {}, "ops": {}, "policies": {}}

        supported_profiles = set(self._dcd.get("conformance_profiles", []))
        negotiation["profile"] = {"eir_profile": prof, "supported": bool(prof in supported_profiles)}

        # Ops support - SpiNNaker supports broader range of ops
        supported_ops = set(self._dcd.get("supported_ops", []))
        emulated_nodes: List[Dict[str, Any]] = []
        total_nodes = 0
        for n in nodes:
            total_nodes += 1
            op = n.get("op")
            if op and op not in supported_ops:
                emulated_nodes.append({"id": n.get("id"), "op": op})

        graph_name = graph.get("name", "graph")
        negotiation["ops"] = {
            "total_nodes": total_nodes,
            "unsupported_ops": sorted({x["op"] for x in emulated_nodes}),
            "emulated_count": len(emulated_nodes),
        }

        plan = {
            "backend": {"name": "spinnaker", "version": self._dcd.get("version", "0.1.0")},
            "graph": {
                "id": graph_name,
                "name": graph_name,
                "profile": prof,
                "seed": eir.get("seed", 0),
            },
            "partitions": [
                {
                    "id": "p0",
                    "nodes": [n.get("id") for n in nodes],
                    "placement": {"chip": 0, "core": 0},  # Hardware placement
                    "resources": {},
                    "emulated": len(emulated_nodes) > 0,
                }
            ],
            "schedule": [
                {
                    "partition_id": "p0",
                    "policy": "event",  # SpiNNaker is event-driven with packet-based timing
                    "dt_us": None,
                    "priority": 0,
                    "affinity": 0,
                }
            ],
            "probes": eir.get("probes", []),
            "epsilons": {"time_us": 1000, "numeric": 1e-4},  # Hardware precision for distributed system
            "warnings": warnings,
            "capabilities": {
                "device": {"name": self._dcd.get("name"), "version": self._dcd.get("version")},
                "supported_ops": sorted(list(supported_ops)),
                "conformance_profiles": sorted(list(supported_profiles)),
                "emulated_nodes": emulated_nodes,
            },
            "negotiation": negotiation,
            "notes": "SpiNNaker distributed neuromorphic computer backend plan",
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
        Execute on SpiNNaker hardware using sPyNNaker.
        """
        if not inputs:
            raise ValueError("at least one input trace is required")
        for input_path in inputs:
            if not os.path.isfile(input_path):
                raise FileNotFoundError(input_path)

        sdk_available = _check_spynnaker()
        if plan is None:
            if sdk_available:
                plan = self.plan(eir)
            else:
                prof, graph, _ = self._validate_eir(eir)
                graph_name = graph.get("name", "graph")
                plan = {
                    "graph": {
                        "id": graph_name,
                        "name": graph_name,
                        "profile": prof,
                        "seed": eir.get("seed", 0),
                    }
                }

        _log.warning("SpiNNaker backend is running in stub mode%s.", "" if sdk_available else " (sPyNNaker unavailable)")

        # Create empty trace for compatibility
        os.makedirs(os.path.dirname(out_trace_path) or ".", exist_ok=True)
        with open(out_trace_path, "w", encoding="utf-8") as out:
            header = {
                "schema_version": SCHEMA_VERSION,
                "dims": ["x", "y", "polarity"],
                "units": {"time": "us", "value": "dimensionless"},
                "dtype": "f32",
                "layout": "coo",
                "metadata": {
                    "backend": "spinnaker",
                    "graph": plan.get("graph", {}).get("id"),
                    "seed": plan.get("graph", {}).get("seed", 0),
                    "hardware_stub": True,
                },
            }
            out.write(json.dumps({"header": header}) + "\n")
            # No events in stub

        return {
            "status": "ok",
            "trace_path": out_trace_path,
            "count": 0,
            "note": "Hardware execution stub - no actual SpiNNaker execution performed",
        }
