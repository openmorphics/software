import unittest; from eventflow_sal.api.packet import *
class TestPacket(unittest.TestCase):
  def test_construct(self):
    p=EventPacket(1000,2,1.5,{"unit":"dB"}); self.assertEqual(p.with_time_offset(500).t_ns, 1500)
    self.assertEqual(dvs_event(10,1,2,1).meta["x"],1)
