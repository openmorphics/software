from __future__ import annotations
from typing import Any, Dict, List, Set

class CertificationProfile:
    def __init__(self, name: str, required_ops: Set[str], constraints: Dict[str, Any]):
        self.name = name
        self.required_ops = required_ops
        self.constraints = constraints

PROFILES = {
    "BASE": CertificationProfile(
        "BASE",
        set(),
        {"max_latency_ms": 100, "deterministic": True}
    ),
    "AUTOMOTIVE_ISO26262": CertificationProfile(
        "AUTOMOTIVE_ISO26262",
        {"lif", "synapse_exp"},
        {"max_latency_ms": 10, "deterministic": True, "redundancy": True}
    ),
    "MEDICAL_IEC62304": CertificationProfile(
        "MEDICAL_IEC62304",
        {"lif"},
        {"max_latency_ms": 50, "deterministic": True, "audit_log": True}
    )
}
