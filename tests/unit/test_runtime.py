import json
import os
import unittest
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
RUNTIME = _load_module_from(os.path.join(BASE_DIR, "eventflow-core", "__init__.py"), "eventflow_core_runtime_test")
VALIDATORS = _load_module_from(os.path.join(BASE_DIR, "eventflow-core", "validators.py"), "eventflow_validators_runtime_test")


class TestRuntime(unittest.TestCase):
    def setUp(self):
        self.out_dir = os.path.join(BASE_DIR, "out")
        os.makedirs(self.out_dir, exist_ok=True)

    def test_compile_and_run_cpu_sim_ok(self):
        eir_path = os.path.join(BASE_DIR, "examples", "wakeword", "eir.json")
        inputs = [os.path.join(BASE_DIR, "examples", "wakeword", "traces", "inputs", "audio_sample.jsonl")]
        trace_out = os.path.join(self.out_dir, "runtime.wakeword.cpu.jsonl")

        res = RUNTIME.compile_and_run(
            eir_path,
            backend="cpu-sim",
            constraints={"inputs": inputs, "trace_out": trace_out},
        )
        self.assertEqual(res.get("status"), "ok", f"runtime failed: {res}")
        self.assertEqual(res.get("backend"), "cpu-sim")
        self.assertTrue(os.path.isfile(trace_out), f"trace not found: {trace_out}")

        # Validate output JSONL trace
        issues = VALIDATORS.validate_event_tensor_jsonl_path(trace_out)
        self.assertEqual(len(issues), 0, f"Trace validation issues: {[str(i) for i in issues]}")

    def test_compile_and_run_missing_inputs(self):
        eir_path = os.path.join(BASE_DIR, "examples", "wakeword", "eir.json")
        trace_out = os.path.join(self.out_dir, "runtime.missing.jsonl")
        with self.assertRaisesRegex(ValueError, "constraints\\.inputs is required"):
            RUNTIME.compile_and_run(eir_path, backend="cpu-sim", constraints={"trace_out": trace_out})


if __name__ == "__main__":
    unittest.main()