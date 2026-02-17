import os
import sys
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG_DIR = os.path.join(BASE_DIR, "eventflow-sal")
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)

from eventflow_sal.api.uri import parse_sensor_uri


class TestURI(unittest.TestCase):
    def test_parse(self):
        uri = parse_sensor_uri("vision.dvs://file/path?foo=bar")
        self.assertEqual(uri.params["foo"], "bar")
