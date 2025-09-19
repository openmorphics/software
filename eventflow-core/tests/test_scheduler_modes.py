import unittest
from typing import Iterator, Tuple, Dict, List

from eventflow_core.eir.ops import ExpSynapse, LIFNeuron
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.runtime.exec import run_event_mode, run_fixed_dt

Event = Tuple[int, int, float, dict]


def stim_ns(ts_list: List[int]) -> Iterator[Event]:
    for t in ts_list:
        # channel 0, value 1.0, empty meta
        yield (t, 0, 1.0, {})


class TestDeterministicSchedulers(unittest.TestCase):
    def _build_simple_graph(self) -> EIRGraph:
        g = EIRGraph()
        g.add_node("n0", ExpSynapse("s0", tau_s="5 ms", weight=1.0).as_op())
        g.add_node("n1", LIFNeuron("l1", tau_m="10 ms", v_th=1.0, v_reset=0.0, r_m=1.0, refractory="2 ms").as_op())
        g.connect("n0", "post", "n1", "in")
        return g

    def test_event_mode_deterministic_replay(self):
        # Use well-separated events to avoid accidental refractory edge behavior
        ts = [1_000_000, 2_000_000, 3_000_000]  # 1ms, 2ms, 3ms
        g = self._build_simple_graph()

        # First run
        out1 = run_event_mode(g, inputs={"n0": stim_ns(ts)})
        # Second run (fresh generator, same timestamps)
        out2 = run_event_mode(g, inputs={"n0": stim_ns(ts)})

        # Outputs for the same graph/input must match exactly
        self.assertIn("n1", out1)
        self.assertIn("n1", out2)
        self.assertEqual(out1["n1"], out2["n1"])

        # Timestamps must be non-decreasing (canonical ordering)
        t_prev = -1
        for ev in out1["n1"]:
            self.assertGreaterEqual(ev[0], t_prev)
            t_prev = ev[0]

        # Expect at least one spike
        self.assertGreater(len(out1["n1"]), 0)

    def test_fixed_step_bucketing_alignment(self):
        ts = [1_000_000, 2_000_000, 3_000_000]
        g = self._build_simple_graph()

        dt_ns = 1_000_000  # 1ms buckets
        out = run_fixed_dt(g, inputs={"n0": stim_ns(ts)}, dt_ns=dt_ns)

        # We should still see outputs on n1
        self.assertIn("n1", out)
        self.assertGreater(len(out["n1"]), 0)

        # Fixed-step scheduler must align times to bucket edges (multiples of dt_ns)
        for ev in out["n1"]:
            self.assertEqual(ev[0] % dt_ns, 0, f"event not aligned to bucket: {ev[0]} % {dt_ns} != 0")

        # Determinism check: re-running yields the same results
        out2 = run_fixed_dt(g, inputs={"n0": stim_ns(ts)}, dt_ns=dt_ns)
        self.assertEqual(out["n1"], out2["n1"])


if __name__ == "__main__":
    unittest.main()