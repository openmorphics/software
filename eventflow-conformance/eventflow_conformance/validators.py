from __future__ import annotations
from typing import Any, Dict, List
from .profiles import PROFILES

class ConformanceValidator:
    def __init__(self, profile_name: str = "BASE"):
        if profile_name not in PROFILES:
            raise ValueError(f"Unknown certification profile: {profile_name}")
        self.profile = PROFILES[profile_name]

    def validate(self, eir_data: Dict[str, Any]) -> List[str]:
        violations = []
        
        # Check profile match
        if eir_data.get("profile") != self.profile.name and self.profile.name != "BASE":
            violations.append(f"EIR profile '{eir_data.get('profile')}' does not match required profile '{self.profile.name}'")

        # Check required ops
        nodes = eir_data.get("nodes", [])
        ops_in_graph = {n.get("op") for n in nodes if n.get("op")}
        for op in self.profile.required_ops:
            if op not in ops_in_graph:
                violations.append(f"Required op '{op}' not found in graph")

        # Check determinism
        if self.profile.constraints.get("deterministic") and not eir_data.get("deterministic", True):
            violations.append("Graph must be deterministic for this profile")

        return violations
