from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import XYToChannel, DelayLine, EventFuse

def event_slam(
    dvs_source: Any,
    imu_source: Any,
    params: Optional[Dict[str, Any]] = None
) -> EIRGraph:
    """
    Minimal SLAM scaffold:
    - Map DVS (x,y) events into linear channels.
    - Delay IMU stream slightly to align temporal correlation.
    - Fuse DVS activity with IMU motion cues within a short window.
    Provide events to nodes:
      - "xy": input stream for DVS events with meta {"x": int, "y": int}
      - "imu": input stream for IMU events
    """
    p = params or {}
    w = int(p.get("width", 128)); h = int(p.get("height", 128))
    imu_delay = p.get("imu_delay", "2 ms")
    window = p.get("window", "5 ms")
    min_count = int(p.get("min_count", 2))

    g = EIRGraph()
    g.add_node("xy", XYToChannel("xy", width=w, height=h).as_op())
    g.add_node("imu", DelayLine("imu", delay="0 ms").as_op())
    g.add_node("delay_imu", DelayLine("delay_imu", delay=imu_delay).as_op())
    g.add_node("slam", EventFuse("slam", window=window, min_count=min_count).as_op())

    g.connect("imu", "out", "delay_imu", "in")
    g.connect("xy", "ch", "slam", "a")
    g.connect("delay_imu", "out", "slam", "b")
    return g
