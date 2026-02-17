from __future__ import annotations

import json
import os
import sys
import unittest
from importlib.resources import files


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for rel in ("eventflow-backends", "eventflow-core"):
    path = os.path.join(BASE_DIR, rel)
    if path not in sys.path:
        sys.path.insert(0, path)


from eventflow_backends import load_backend


class TestPackagedResources(unittest.TestCase):
    def test_dcd_resources_are_loadable_via_importlib_resources(self):
        targets = (
            ("eventflow_backends.cpu_sim", "cpu-sim"),
            ("eventflow_backends.gpu_sim", "gpu-sim"),
            ("eventflow_backends.vendor_backends.loihi", "loihi"),
            ("eventflow_backends.vendor_backends.spinnaker", "spinnaker"),
            ("eventflow_backends.vendor_backends.synsense", "synsense"),
        )
        for package, expected_name in targets:
            with self.subTest(package=package):
                payload = files(package).joinpath("dcd.json").read_text(encoding="utf-8")
                dcd = json.loads(payload)
                self.assertEqual(dcd.get("name"), expected_name)
                self.assertIn("deterministic_modes", dcd)
                self.assertIn("supported_ops", dcd)

    def test_builtin_backends_load_with_packaged_dcd(self):
        cpu = load_backend("cpu-sim")
        gpu = load_backend("gpu-sim")

        self.assertEqual(cpu.name(), "cpu-sim")
        self.assertEqual(gpu.name(), "gpu-sim")
        self.assertEqual(cpu.dcd().get("name"), "cpu-sim")
        self.assertEqual(gpu.dcd().get("name"), "gpu-sim")


if __name__ == "__main__":
    unittest.main()
