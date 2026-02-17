import unittest
import os
import sys
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CLI = os.path.join(ROOT, "eventflow-cli", "ef.py")


class TestCLISmoke(unittest.TestCase):
    def test_subcommands_exist(self):
        p = subprocess.run([sys.executable, "-u", CLI, "--help"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, msg=p.stderr)
        for cmd in ("build", "run", "profile", "validate", "compare-traces", "sal-stream"):
            self.assertIn(cmd, p.stdout)

    def test_legacy_validate_alias_removed(self):
        p = subprocess.run([sys.executable, "-u", CLI, "validate-eir", "--path", "x"], capture_output=True, text=True)
        self.assertEqual(p.returncode, 2)
