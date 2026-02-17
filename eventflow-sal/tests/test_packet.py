import os
import sys
import unittest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG_DIR = os.path.join(BASE_DIR, "eventflow-sal")
if PKG_DIR not in sys.path:
    sys.path.insert(0, PKG_DIR)

from eventflow_sal.api.packet import EventPacket, dvs_event


class TestPacket(unittest.TestCase):
    def test_construct(self):
        pkt = EventPacket(1000, 2, 1.5, {"unit": "dB"})
        self.assertEqual(pkt.with_time_offset(500).t_ns, 1500)
        self.assertEqual(dvs_event(10, 1, 2, 1).meta["x"], 1)
