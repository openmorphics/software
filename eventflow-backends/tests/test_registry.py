import unittest
from eventflow_backends import get_backend
from eventflow_backends.api import Backend

class TestRegistry(unittest.TestCase):
    def test_get_backend(self):
        b = get_backend("cpu_sim")
        self.assertIsInstance(b, Backend)
        self.assertEqual(b.id, "cpu_sim")
    def test_unknown(self):
        with self.assertRaises(KeyError):
            get_backend("nope")
