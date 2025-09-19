import unittest
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import XYToChannel, ShiftXY
from eventflow_core.runtime.exec import run_event_mode

def dvs_points(ts, xs, ys):
    for t, x, y in zip(ts, xs, ys):
        yield (t, 0, 1.0, {"unit": "pol", "x": int(x), "y": int(y)})

class TestXYOps(unittest.TestCase):
    def test_xy_to_channel_maps_xy_to_linear_channel(self):
        w, h = 8, 8
        g = EIRGraph()
        g.add_node("xy", XYToChannel("xy", width=w, height=h).as_op())

        out = run_event_mode(g, {"xy": dvs_points([1_000_000], [3], [2])})
        self.assertEqual(len(out["xy"]), 1)
        t, ch, val, meta = out["xy"][0]
        self.assertEqual(ch, 2 * w + 3)
        self.assertAlmostEqual(val, 1.0, places=6)
        self.assertEqual(meta.get("w"), w)
        self.assertEqual(meta.get("h"), h)

    def test_shift_xy_dx_positive(self):
        w, h = 8, 8
        g = EIRGraph()
        g.add_node("xy", XYToChannel("xy", width=w, height=h).as_op())
        g.add_node("shift", ShiftXY("shift", dx=1, dy=0, width=w, height=h).as_op())
        g.connect("xy", "ch", "shift", "in")

        out = run_event_mode(g, {"xy": dvs_points([1_000_000], [3], [2])})
        self.assertEqual(len(out["shift"]), 1)
        _, ch, _, _ = out["shift"][0]
        self.assertEqual(ch, 2 * w + 4)

    def test_shift_xy_clamps_edges(self):
        w, h = 8, 8
        g = EIRGraph()
        g.add_node("xy", XYToChannel("xy", width=w, height=h).as_op())
        g.add_node("shift", ShiftXY("shift", dx=-1, dy=-1, width=w, height=h).as_op())
        g.connect("xy", "ch", "shift", "in")

        # At (0,0), shifting -1,-1 should clamp back to (0,0)
        out = run_event_mode(g, {"xy": dvs_points([1_000_000], [0], [0])})
        self.assertEqual(len(out["shift"]), 1)
        _, ch, _, _ = out["shift"][0]
        self.assertEqual(ch, 0)