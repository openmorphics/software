import unittest
import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
for rel in ("eventflow-backends", "eventflow-core"):
    path = os.path.join(BASE_DIR, rel)
    if path not in sys.path:
        sys.path.insert(0, path)

from eventflow_backends import get_backend, list_backends, load_backend

class TestRegistry(unittest.TestCase):
    def test_get_backend(self):
        b = get_backend("cpu_sim")
        self.assertEqual(b.name(), "cpu-sim")

    def test_list_backends(self):
        names = list_backends()
        self.assertIn("cpu-sim", names)
        self.assertIn("gpu-sim", names)

    def test_unknown(self):
        with self.assertRaises(ValueError):
            load_backend("nope")
