import os, json, tarfile, tempfile, shutil, unittest
from eventflow_hub.pack import pack_bundle, unpack_bundle

class TestPack(unittest.TestCase):
    def test_pack_and_unpack(self):
        with tempfile.TemporaryDirectory() as d:
            # create required files
            with open(os.path.join(d, "model.eir"), "w") as f: f.write("{}")
            with open(os.path.join(d, "cap.json"), "w") as f: json.dump({}, f)
            with open(os.path.join(d, "trace.json"), "w") as f: json.dump({}, f)
            with open(os.path.join(d, "card.json"), "w") as f: json.dump({}, f)

            out = os.path.join(d, "bundle.tar.gz")
            tar_path = pack_bundle(d, out)
            self.assertTrue(os.path.exists(tar_path))

            dest = os.path.join(d, "unpacked")
            unpack_bundle(tar_path, dest)
            for f in ("model.eir","cap.json","trace.json","card.json"):
                self.assertTrue(os.path.exists(os.path.join(dest, f)))
