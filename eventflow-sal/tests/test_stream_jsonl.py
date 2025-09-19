from __future__ import annotations
import io, json, os, tempfile, unittest
from typing import List

from eventflow_sal import __name__ as _pkg  # ensure package import works
# High-level SAL API we added
from eventflow_sal import open as _unused  # noqa: F401 just to assert module exists
import importlib.util
import importlib.machinery
import types


def _load_sal_api_top() -> types.ModuleType:
    """
    Load top-level SAL API module (eventflow-sal/api.py) to access stream_to_jsonl
    without relying on sys.path package layout in tests.
    """
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sal_api_path = os.path.join(root, "eventflow-sal", "api.py")
    if not os.path.isfile(sal_api_path):
        raise FileNotFoundError(f"SAL API not found at {sal_api_path}")
    spec = importlib.util.spec_from_file_location("eventflow_sal_top_api", sal_api_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


class TestSALStreamJSONL(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def _write_jsonl(self, path: str, events: List[dict]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            header = {
                "header": {
                    "schema_version": "0.1.0",
                    "dims": ["x", "y", "polarity"],
                    "units": {"time": "us", "value": "dimensionless"},
                    "dtype": "f32",
                    "layout": "coo",
                    "metadata": {"kind": "vision.dvs", "file": os.path.basename(path)},
                }
            }
            f.write(json.dumps(header) + "\n")
            for ev in events:
                f.write(json.dumps(ev) + "\n")

    def test_passthrough_normalization_dvs_jsonl(self):
        # Prepare a tiny DVS JSONL
        src_path = os.path.join(self.tmpdir.name, "in.jsonl")
        out_path = os.path.join(self.tmpdir.name, "out.jsonl")
        tel_path = os.path.join(self.tmpdir.name, "tele.json")
        events = [
            {"ts": 0, "idx": [1, 2, 1], "val": 1.0},
            {"ts": 1000, "idx": [2, 2, 1], "val": 1.0},
            {"ts": 2000, "idx": [3, 2, 1], "val": 1.0},
        ]
        self._write_jsonl(src_path, events)

        # Use top-level SAL API (eventflow-sal/api.py) to stream
        sal_api = _load_sal_api_top()
        tele = sal_api.stream_to_jsonl(
            f"vision.dvs://file?format=jsonl&path={src_path}",
            out_path,
            telemetry_out=tel_path,
        )
        # Telemetry fields
        self.assertTrue(tele.get("normalized", False))
        self.assertEqual(tele.get("count"), len(events))
        self.assertIn("duration_us", tele)
        self.assertIn("events_per_second", tele)
        self.assertIn("dt", tele)
        self.assertIn("clock", tele)
        # Jitter statistics should be present when telemetry is computed
        for k in ("jitter_p50_us", "jitter_p95_us", "jitter_p99_us"):
            self.assertIn(k, tele["clock"])

        # Telemetry file exists and matches dict
        with open(tel_path, "r", encoding="utf-8") as f:
            tele2 = json.load(f)
        self.assertEqual(tele["count"], tele2["count"])

        # Output JSONL header + events
        with open(out_path, "r", encoding="utf-8") as f:
            first = f.readline(); self.assertTrue(first, "missing header")
            obj = json.loads(first)
            self.assertIn("header", obj)
            # Validate a couple of records exist
            rec_count = sum(1 for _ in f)
            self.assertEqual(rec_count, len(events))

    def test_header_synthesis_when_missing(self):
        # No header: write raw events only
        src_path = os.path.join(self.tmpdir.name, "raw.jsonl")
        out_path = os.path.join(self.tmpdir.name, "out2.jsonl")
        with open(src_path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"ts": 0, "idx": [0], "val": 1.0}) + "\n")
            f.write(json.dumps({"ts": 100, "idx": [1], "val": 2.0}) + "\n")

        sal_api = _load_sal_api_top()
        tele = sal_api.stream_to_jsonl(
            f"vision.dvs://file?format=jsonl&path={src_path}",
            out_path,
        )
        self.assertTrue(tele.get("normalized", False))
        # Ensure header present in output
        with open(out_path, "r", encoding="utf-8") as f:
            obj = json.loads(f.readline())
            self.assertIn("header", obj)


if __name__ == "__main__":
    unittest.main()