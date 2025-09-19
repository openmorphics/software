import unittest; from eventflow_sal.api.uri import parse_sensor_uri
class TestURI(unittest.TestCase):
  def test_parse(self):
    u=parse_sensor_uri("vision.dvs://file/path?foo=bar"); self.assertEqual(u.params["foo"],"bar")
