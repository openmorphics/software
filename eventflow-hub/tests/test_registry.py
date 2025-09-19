import os, json, tempfile, unittest
from eventflow_hub.pack import pack_bundle
from eventflow_hub.registry import LocalRegistry

class TestRegistry(unittest.TestCase):
    def test_add_and_get(self):
        with tempfile.TemporaryDirectory() as d:
            # create a bundle
            src = os.path.join(d, "src")
            os.makedirs(src)
            with open(os.path.join(src, "model.eir"), "w") as f: f.write("{}")
            with open(os.path.join(src, "cap.json"), "w") as f: json.dump({}, f)
            with open(os.path.join(src, "trace.json"), "w") as f: json.dump({}, f)
            with open(os.path.join(src, "card.json"), "w") as f: json.dump({}, f)
            bundle = pack_bundle(src, os.path.join(d, "bundle.tar.gz"))

            reg = LocalRegistry(os.path.join(d, "reg"))
            key = reg.add("mymodel", "1.0.0", bundle)
            self.assertEqual(key, "mymodel:1.0.0")
            path = reg.get("mymodel", "1.0.0")
            self.assertTrue(os.path.exists(path))
            self.assertIn("mymodel:1.0.0", reg.list())
