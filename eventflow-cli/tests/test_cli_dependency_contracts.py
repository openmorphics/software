from __future__ import annotations

import argparse
import builtins
import io
import importlib
import json
import os
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for rel in ("eventflow-cli",):
    path = os.path.join(ROOT, rel)
    if path not in sys.path:
        sys.path.insert(0, path)

cli_main = importlib.import_module("eventflow_cli.main")


class TestCliDependencyContracts(unittest.TestCase):
    def _capture_exit(self, fn, args: argparse.Namespace):
        out = io.StringIO()
        err = io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            with self.assertRaises(SystemExit) as cm:
                fn(args)
        return cm.exception.code, out.getvalue().strip(), err.getvalue().strip()

    def _import_blocker(self, blocked_prefixes: tuple[str, ...]):
        original_import = builtins.__import__

        def _wrapped(name, globals=None, locals=None, fromlist=(), level=0):
            if any(name == pref or name.startswith(pref + ".") for pref in blocked_prefixes):
                raise ImportError(f"blocked import for test: {name}")
            return original_import(name, globals, locals, fromlist, level)

        return _wrapped

    def test_validate_reports_dependency_import_failure_as_exit_2_json(self):
        cli_main.CLI_JSON = True
        args = argparse.Namespace(eir="dummy.json", event=None, trace=None, dcd=None, efpkg=None, root=None, format="auto")
        with patch("eventflow_cli.main._ensure_repo_paths", lambda: None):
            with patch("builtins.__import__", new=self._import_blocker(("eventflow_core",))):
                code, out, err = self._capture_exit(cli_main.cmd_validate, args)

        self.assertEqual(code, 2)
        self.assertEqual(err, "")
        payload = json.loads(out)
        self.assertFalse(payload.get("ok", True))
        self.assertIn("failed to import validators", payload.get("error", ""))

    def test_run_reports_backend_import_failure_as_exit_2_json(self):
        cli_main.CLI_JSON = True
        args = argparse.Namespace(eir="dummy.json", backend="cpu-sim", input=["in.jsonl"], trace_out="out.jsonl", plan=None)
        with patch("eventflow_cli.main._ensure_repo_paths", lambda: None):
            with patch("builtins.__import__", new=self._import_blocker(("eventflow_backends",))):
                code, out, err = self._capture_exit(cli_main.cmd_run, args)

        self.assertEqual(code, 2)
        self.assertEqual(err, "")
        payload = json.loads(out)
        self.assertFalse(payload.get("ok", True))
        self.assertIn("failed to load backend registry", payload.get("error", ""))


if __name__ == "__main__":
    unittest.main()
