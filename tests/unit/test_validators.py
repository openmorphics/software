import json
import os
import unittest

# Import validators via direct path to avoid packaging issues in scaffold
import importlib.util
from typing import Any, List


def _load_module_from(path: str, name: str):
    """
    Load a module from a file path and ensure it is registered in sys.modules
    before execution so dataclasses and typing introspection work correctly.
    """
    import sys
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module {name} from {path}")
    mod = importlib.util.module_from_spec(spec)  # type: ignore
    # Register in sys.modules before executing to satisfy dataclasses typing
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore
    return mod


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
VALIDATORS = _load_module_from(os.path.join(BASE_DIR, "eventflow-core", "validators.py"), "eventflow_validators")


class TestValidators(unittest.TestCase):
    def test_validate_eir_ok(self):
        path = os.path.join(BASE_DIR, "examples", "wakeword", "eir.json")
        with open(path, "r", encoding="utf-8") as f:
            eir = json.load(f)
        issues = VALIDATORS.validate_eir(eir)
        self.assertEqual(len(issues), 0, f"Unexpected EIR validation issues: {[str(i) for i in issues]}")

    def test_validate_event_tensor_jsonl_ok(self):
        path = os.path.join(BASE_DIR, "examples", "wakeword", "traces", "inputs", "audio_sample.jsonl")
        issues = VALIDATORS.validate_event_tensor_jsonl_path(path)
        self.assertEqual(len(issues), 0, f"Unexpected Event Tensor issues: {[str(i) for i in issues]}")

    def test_validate_event_tensor_jsonl_monotonic_violation(self):
        # Create a small malformed JSONL in-memory and write to temp file
        tmp = os.path.join(BASE_DIR, "out", "tmp.nonmonotonic.jsonl")
        os.makedirs(os.path.dirname(tmp), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(json.dumps({"header": {"schema_version": "0.1.0", "dims": ["band"], "units": {"time": "ms", "value": "dB"}, "dtype": "f16", "layout": "coo"}}) + "\n")
            f.write(json.dumps({"ts": 20, "idx": [0], "val": 1.0}) + "\n")
            f.write(json.dumps({"ts": 10, "idx": [0], "val": 1.0}) + "\n")  # backwards timestamp
        issues = VALIDATORS.validate_event_tensor_jsonl_path(tmp)
        self.assertTrue(any("timestamps not non-decreasing" in str(i) for i in issues), f"Expected monotonic error, got: {[str(i) for i in issues]}")

    def test_validate_dcd_ok(self):
        cpu_dcd = os.path.join(BASE_DIR, "eventflow-backends", "cpu_sim", "dcd.json")
        with open(cpu_dcd, "r", encoding="utf-8") as f:
            dcd = json.load(f)
        issues = VALIDATORS.validate_dcd(dcd)
        self.assertEqual(len(issues), 0, f"Unexpected DCD validation issues: {[str(i) for i in issues]}")

    def test_validate_efpkg_roundtrip(self):
        # Build a minimal manifest referencing existing artifacts
        eir_path = os.path.join(BASE_DIR, "examples", "wakeword", "eir.json")
        golden_path = os.path.join(BASE_DIR, "out", "wakeword.golden.jsonl")
        if not os.path.isfile(golden_path):
            self.skipTest("Golden trace not generated yet; run ef run first")
        man = {
            "schema_version": "0.1.0",
            "sdk_version": "0.1.0",
            "created_at": "2025-01-01T00:00:00Z",
            "model": {"id": "test.model", "name": "Test Model"},
            "profile": {"name": "BASE"},
            "determinism": {"time_unit": "us", "mode": "fixed_step", "fixed_step_dt_us": 100, "epsilon_time_us": 100, "epsilon_numeric": 1e-5, "seed": 0},
            "features": [],
            "capabilities_required": {},
            "artifacts": {
                "eir": {"path": os.path.relpath(eir_path, os.path.dirname(golden_path)), "format": "json"},
                "traces": {"golden": {"path": os.path.basename(golden_path), "format": "jsonl"}},
            },
        }
        # Write manifest next to golden
        man_path = os.path.join(os.path.dirname(golden_path), "test.efpkg.json")
        with open(man_path, "w", encoding="utf-8") as f:
            json.dump(man, f)
        issues = VALIDATORS.validate_efpkg(man, root_dir=os.path.dirname(golden_path))
        self.assertEqual(len(issues), 0, f"Unexpected EFPKG issues: {[str(i) for i in issues]}")


if __name__ == "__main__":
    unittest.main()