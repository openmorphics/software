from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
import unittest


def _run_ef(args: list[str]) -> tuple[int, str, str]:
    # Run the repo-local ef CLI with --json enabled
    cmd = [sys.executable, "-u", "eventflow-cli/ef.py", "--json"] + args
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = p.communicate()
    return p.returncode, out.strip(), err.strip()


class TestEfCliJson(unittest.TestCase):
    def test_version_json(self):
        rc, out, err = _run_ef(["version"])
        self.assertEqual(rc, 0, msg=err)
        data = json.loads(out)
        self.assertIn("version", data)

    def test_list_backends_json(self):
        rc, out, err = _run_ef(["list-backends"])
        self.assertEqual(rc, 0, msg=err)
        data = json.loads(out)
        self.assertIn("backends", data)
        self.assertTrue(any(b in ("cpu-sim", "gpu-sim") for b in data["backends"]))

    def test_compare_traces_json(self):
        with tempfile.TemporaryDirectory() as td:
            # Write minimal JSONL with header and a few events
            a = os.path.join(td, "a.jsonl")
            b = os.path.join(td, "b.jsonl")
            header = {
                "header": {
                    "schema_version": "0.1.0",
                    "dims": ["ch"],
                    "units": {"time": "us", "value": "dimensionless"},
                    "dtype": "f32",
                    "layout": "coo",
                    "metadata": {"test": "ef_cli_json"},
                }
            }
            events = [
                {"ts": 0, "idx": [0], "val": 1.0},
                {"ts": 100, "idx": [0], "val": 2.0},
                {"ts": 200, "idx": [1], "val": 3.0},
            ]
            for p in (a, b):
                with open(p, "w", encoding="utf-8") as f:
                    f.write(json.dumps(header) + "\n")
                    for e in events:
                        f.write(json.dumps(e) + "\n")
            rc, out, err = _run_ef(["compare-traces", "--golden", a, "--candidate", b])
            self.assertEqual(rc, 0, msg=err)
            data = json.loads(out)
            self.assertTrue(data.get("ok", False))


if __name__ == "__main__":
    unittest.main()