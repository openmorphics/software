from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
import unittest


def _run_ef(args: list[str]) -> tuple[int, str, str]:
    cmd = [sys.executable, "-u", "eventflow-cli/ef.py", "--json"] + args
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate()
    return p.returncode, out.strip(), err.strip()


class TestEfCliSalAndRun(unittest.TestCase):
    def test_sal_stream_passthrough_dvs(self):
        with tempfile.TemporaryDirectory() as td:
            src = os.path.join(td, "in.jsonl")
            out = os.path.join(td, "out.jsonl")
            tele = os.path.join(td, "tele.json")
            header = {
                "header": {
                    "schema_version": "0.1.0",
                    "dims": ["x", "y", "polarity"],
                    "units": {"time": "us", "value": "dimensionless"},
                    "dtype": "f32",
                    "layout": "coo",
                    "metadata": {"test": "sal_passthrough"},
                }
            }
            events = [
                {"ts": 0, "idx": [1, 2, 1], "val": 1.0},
                {"ts": 1000, "idx": [2, 2, 1], "val": 1.0},
                {"ts": 2000, "idx": [3, 2, 1], "val": 1.0},
            ]
            with open(src, "w", encoding="utf-8") as f:
                f.write(json.dumps(header) + "\n")
                for e in events:
                    f.write(json.dumps(e) + "\n")

            rc, out_json, err = _run_ef([
                "sal-stream",
                "--uri", f"vision.dvs://file?format=jsonl&path={src}",
                "--out", out,
                "--telemetry-out", tele,
            ])
            self.assertEqual(rc, 0, msg=err)
            # ef outputs JSON doc when --json flag is set
            meta = json.loads(out_json)
            self.assertIn("out", meta)
            self.assertTrue(os.path.isfile(meta["out"]))
            # Telemetry exists
            self.assertTrue(os.path.isfile(tele))
            with open(tele, "r", encoding="utf-8") as tf:
                tele_obj = json.load(tf)
            self.assertEqual(tele_obj.get("count"), len(events))
            self.assertIn("clock", tele_obj)
            # Jitter fields (added)
            for k in ("jitter_p50_us", "jitter_p95_us", "jitter_p99_us"):
                self.assertIn(k, tele_obj["clock"])

    def test_run_cpu_sim_with_examples(self):
        # Use provided example artifacts: vision optical flow EIR and sample input JSONL
        eir_path = "examples/vision_optical_flow/eir.json"
        inp_path = "examples/vision_optical_flow/traces/inputs/vision_sample.jsonl"
        self.assertTrue(os.path.isfile(eir_path), "missing example EIR")
        self.assertTrue(os.path.isfile(inp_path), "missing example input")
        with tempfile.TemporaryDirectory() as td:
            trace_out = os.path.join(td, "trace.jsonl")
            rc, out_json, err = _run_ef([
                "run",
                "--eir", eir_path,
                "--backend", "cpu-sim",
                "--input", inp_path,
                "--trace-out", trace_out,
            ])
            self.assertEqual(rc, 0, msg=err)
            data = json.loads(out_json)
            self.assertEqual(data.get("status"), "ok")
            self.assertTrue(os.path.isfile(data.get("trace_path", "")))
            self.assertGreaterEqual(int(data.get("count", 0)), 1)


if __name__ == "__main__":
    unittest.main()