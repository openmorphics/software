import json
import os
import unittest
import tempfile
from typing import Any, List


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for rel in ("eventflow-core", "eventflow-backends"):
    path = os.path.join(BASE_DIR, rel)
    if path not in os.sys.path:
        os.sys.path.insert(0, path)

from eventflow_core import compile_and_run
from eventflow_core import validators


class TestRuntime(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.out_dir = self.tempdir.name

    def test_compile_and_run_cpu_sim_ok(self):
        eir_path = os.path.join(BASE_DIR, "examples", "wakeword", "eir.json")
        inputs = [os.path.join(BASE_DIR, "examples", "wakeword", "traces", "inputs", "audio_sample.jsonl")]
        trace_out = os.path.join(self.out_dir, "runtime.wakeword.cpu.jsonl")

        res = compile_and_run(
            eir_path,
            backend="cpu-sim",
            constraints={"inputs": inputs, "trace_out": trace_out},
        )
        self.assertEqual(res.get("status"), "ok", f"runtime failed: {res}")
        self.assertEqual(res.get("backend"), "cpu-sim")
        self.assertTrue(os.path.isfile(trace_out), f"trace not found: {trace_out}")

        # Validate output JSONL trace
        issues = validators.validate_event_tensor_jsonl_path(trace_out)
        self.assertEqual(len(issues), 0, f"Trace validation issues: {[str(i) for i in issues]}")

    def test_compile_and_run_missing_inputs(self):
        eir_path = os.path.join(BASE_DIR, "examples", "wakeword", "eir.json")
        trace_out = os.path.join(self.out_dir, "runtime.missing.jsonl")
        with self.assertRaisesRegex(ValueError, "constraints\\.inputs is required"):
            compile_and_run(eir_path, backend="cpu-sim", constraints={"trace_out": trace_out})


if __name__ == "__main__":
    unittest.main()
