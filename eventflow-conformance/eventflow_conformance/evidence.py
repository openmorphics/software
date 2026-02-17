from __future__ import annotations
import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

class EvidenceExporter:
    def __init__(self, eir_path: str):
        self.eir_path = eir_path
        self._eir_hash = self._hash_file(eir_path)

    def _hash_file(self, path: str) -> str:
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256.update(byte_block)
        return sha256.hexdigest()

    def generate_report(self, 
                        profile: str, 
                        violations: List[str], 
                        backend_info: Dict[str, Any],
                        org_name: str) -> Dict[str, Any]:
        return {
            "report_id": hashlib.md5(f"{self.eir_path}-{datetime.now().isoformat()}".encode()).hexdigest(),
            "timestamp": datetime.now().isoformat(),
            "organization": org_name,
            "target": {
                "eir_path": self.eir_path,
                "eir_sha256": self._eir_hash,
            },
            "environment": {
                "backend": backend_info,
            },
            "conformance": {
                "profile": profile,
                "status": "PASSED" if not violations else "FAILED",
                "violations": violations,
            }
        }

    def export(self, report: Dict[str, Any], output_path: str) -> None:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
