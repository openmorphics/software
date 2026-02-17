import os
import sys
import tempfile
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG_DIR = os.path.join(BASE_DIR, "eventflow-sal")
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)

from eventflow_sal.drivers.dvs import AEDAT4FileSource


class TestReplay(unittest.TestCase):
    def test_dvs(self):
        with tempfile.NamedTemporaryFile(suffix=".aedat4", delete=False) as f:
            path = f.name
        try:
            src = AEDAT4FileSource(path)
            evs = list(src.subscribe())
            self.assertEqual(len(evs), 1000)
        finally:
            os.remove(path)
