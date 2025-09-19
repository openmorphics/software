import unittest, os, tempfile; from eventflow_sal.drivers.dvs import AEDAT4FileSource
class TestReplay(unittest.TestCase):
  def test_dvs(self):
    with tempfile.NamedTemporaryFile(suffix=".aedat4",delete=False) as f:
      src=AEDAT4FileSource(f.name); evs=list(src.subscribe())
      self.assertEqual(len(evs), 1000)
    os.remove(f.name)
