import unittest

from eventflow_core.runtime.exec import run_event_mode
from eventflow_modules.vision import optical_flow, corner_tracking, object_tracking
from eventflow_modules.robotics import event_slam
from eventflow_modules.timeseries import change_point, spike_pattern_mining
from eventflow_modules.wellness import sleep_staging, stress_index
from eventflow_modules.creative import bio_sequencer


def dvs_stream_east(width=8, height=8, y=2, n=3, step_ms=1):
    # Emit n events moving east along row y with step_ms between events
    for i in range(n):
        t_ns = i * step_ms * 1_000_000
        x = min(i + 1, width - 1)
        yield (t_ns, 0, 1.0, {"unit": "pol", "x": x, "y": y})


def dvs_single(x=3, y=3, t_ns=1_000_000):
    yield (t_ns, 0, 1.0, {"unit": "pol", "x": x, "y": y})


def impulses(times_ns):
    for t in times_ns:
        yield (t, 0, 1.0, {"unit": "evt"})


class TestVisionModules(unittest.TestCase):
    def test_optical_flow_east_coincidence(self):
        g = optical_flow(
            None,
            window="2 ms",
            min_coincidences=1,
            params={"width": 8, "height": 8, "delay": "1 ms"},
        )
        out = run_event_mode(g, {"xy": dvs_stream_east(width=8, height=8, y=2, n=3, step_ms=1)})
        # Expect eastward flow coincidences
        self.assertIn("flow_e", out)
        self.assertGreaterEqual(len(out["flow_e"]), 1)

    def test_corner_tracking_shift_orthogonal(self):
        g = corner_tracking(None, window="2 ms", params={"width": 8, "height": 8})
        out = run_event_mode(g, {"xy": dvs_single(x=3, y=3)})
        self.assertIn("corners", out)
        self.assertGreaterEqual(len(out["corners"]), 1)

    def test_object_tracking_persistence(self):
        g = object_tracking(None, window="5 ms", params={"width": 8, "height": 8, "delay": "2 ms"})
        out = run_event_mode(g, {"xy": dvs_single(x=1, y=1, t_ns=1_000_000)})
        self.assertIn("track", out)
        self.assertGreaterEqual(len(out["track"]), 1)


class TestRoboticsModules(unittest.TestCase):
    def test_event_slam_fuse(self):
        g = event_slam(None, None, params={"width": 8, "height": 8, "imu_delay": "1 ms", "window": "3 ms", "min_count": 1})
        # DVS event at 1ms, IMU event at 1ms (delayed to 2ms), within window 3ms
        out = run_event_mode(g, {
            "xy": dvs_single(x=2, y=2, t_ns=1_000_000),
            "imu": impulses([1_000_000]),
        })
        self.assertIn("slam", out)
        self.assertGreaterEqual(len(out["slam"]), 1)


class TestTimeseriesWellnessCreative(unittest.TestCase):
    def test_change_point_self_coincidence(self):
        g = change_point(None, window="2 ms", min_events=2)
        # Two impulses separated by 2ms
        out = run_event_mode(g, {"id": impulses([0, 2_000_000])})
        self.assertIn("cpd", out)
        self.assertGreaterEqual(len(out["cpd"]), 1)

    def test_spike_pattern_mining(self):
        g = spike_pattern_mining(None, params={"window": "1 ms", "min_count": 2})
        out = run_event_mode(g, {"id": impulses([0, 1_000_000])})
        self.assertIn("mine", out)
        self.assertGreaterEqual(len(out["mine"]), 1)

    def test_sleep_staging_epoch(self):
        g = sleep_staging(None, window="5 ms")
        out = run_event_mode(g, {"id": impulses([0, 5_000_000])})
        self.assertIn("sleep", out)
        self.assertGreaterEqual(len(out["sleep"]), 1)

    def test_stress_index_three_within_window(self):
        g = stress_index(None, window="5 ms")
        # Two id events at 0ms and 1ms, delayed copy at 5ms -> total 3 within window
        out = run_event_mode(g, {"id": impulses([0, 1_000_000])})
        self.assertIn("stress", out)
        self.assertGreaterEqual(len(out["stress"]), 1)

    def test_bio_sequencer_tempo(self):
        g = bio_sequencer(None, tempo="5 ms")
        out = run_event_mode(g, {"id": impulses([0])})
        self.assertIn("sequencer", out)
        self.assertGreaterEqual(len(out["sequencer"]), 1)


if __name__ == "__main__":
    unittest.main()