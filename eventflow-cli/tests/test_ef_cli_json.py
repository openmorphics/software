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

    def test_validate_grouped_json(self):
        eir = "examples/wakeword/eir.json"
        rc, out, err = _run_ef(["validate", "--eir", eir])
        self.assertEqual(rc, 0, msg=err)
        data = json.loads(out)
        self.assertTrue(data.get("ok", False))

    def test_run_unknown_backend_returns_runtime_contract(self):
        eir_path = "examples/wakeword/eir.json"
        inp_path = "examples/wakeword/traces/inputs/audio_sample.jsonl"
        with tempfile.TemporaryDirectory() as td:
            trace_out = os.path.join(td, "trace.jsonl")
            rc, out, err = _run_ef(
                [
                    "run",
                    "--eir",
                    eir_path,
                    "--backend",
                    "definitely-not-a-backend",
                    "--input",
                    inp_path,
                    "--trace-out",
                    trace_out,
                ]
            )
            self.assertEqual(rc, 1)
            self.assertEqual(err, "")
            data = json.loads(out)
            self.assertFalse(data.get("ok", True))
            self.assertIn("backend run failed", data.get("error", ""))

    def test_hub_registry_uses_env_when_flag_missing(self):
        with tempfile.TemporaryDirectory() as env_root:
            cmd = [sys.executable, "-u", "eventflow-cli/ef.py", "--json", "hub", "list"]
            env = os.environ.copy()
            env["EF_HUB_ROOT"] = env_root
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
            out, err = p.communicate()
            self.assertEqual(p.returncode, 0, msg=err)
            data = json.loads(out)
            self.assertIn("packages", data)
            self.assertTrue(os.path.isdir(os.path.join(env_root, "packages")))

    def test_hub_registry_flag_overrides_env(self):
        with tempfile.TemporaryDirectory() as env_root, tempfile.TemporaryDirectory() as flag_root:
            cmd = [
                sys.executable,
                "-u",
                "eventflow-cli/ef.py",
                "--json",
                "hub",
                "--registry",
                flag_root,
                "list",
            ]
            env = os.environ.copy()
            env["EF_HUB_ROOT"] = env_root
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
            out, err = p.communicate()
            self.assertEqual(p.returncode, 0, msg=err)
            data = json.loads(out)
            self.assertIn("packages", data)
            self.assertTrue(os.path.isdir(os.path.join(flag_root, "packages")))
            self.assertFalse(os.path.isdir(os.path.join(env_root, "packages")))

    def test_hub_info_missing_returns_json_error(self):
        with tempfile.TemporaryDirectory() as hub_root:
            cmd = [
                sys.executable,
                "-u",
                "eventflow-cli/ef.py",
                "--json",
                "hub",
                "--registry",
                hub_root,
                "info",
                "missing",
            ]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            out, err = p.communicate()
            self.assertEqual(p.returncode, 1)
            self.assertEqual(err.strip(), "")
            data = json.loads(out)
            self.assertFalse(data.get("ok", True))
            self.assertIn("error", data)


if __name__ == "__main__":
    unittest.main()
