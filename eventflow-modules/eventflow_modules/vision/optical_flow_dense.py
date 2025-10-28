from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, XYToChannel, ShiftXY

def optical_flow_dense(
    source: Any,
    window: str = "2 ms",
    dirs: int = 8,
    radius: int = 1,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Dense optical flow proxy using spatial shifts and temporal alignment.

    Constructs a graph that detects motion by coincident activity between the current
    XY channelized events and a spatially shifted, delayed copy for multiple directions.

    Nodes and ports:
      - "xy": XYToChannel(width,height) expects (x,y) metadata events at runtime: meta {"x": int, "y": int}
      - For each direction D in {e,w,n,s,(optional: ne,nw,se,sw)}:
          shift_D: ShiftXY(dx,dy,width,height)
          delay_D: DelayLine(delay)
          flow_D:  EventFuse(window,min_count=1) with inputs (a: xy.ch, b: delay_D.out)

    Parameters:
      - window: coincidence window (e.g., "2 ms")
      - dirs:  number of directions (4 or 8). 4 = {e,w,n,s}, 8 = add {ne,nw,se,sw}
      - radius: integer radius multiplier for spatial shift (>=1)
      - params:
          width (int), height (int)   — required for XYToChannel and bounds in ShiftXY
          delay (str)                 — temporal alignment delay (default "1 ms")

    Returns:
      EIRGraph with named outputs:
        - "flow_e", "flow_w", "flow_n", "flow_s", and optionally diagonals "flow_ne", "flow_nw", "flow_se", "flow_sw".
    """
    p = params or {}
    w = int(p.get("width", 128))
    h = int(p.get("height", 128))
    delay = p.get("delay", "1 ms")

    if dirs not in (4, 8):
        # normalize to supported set
        dirs = 8 if dirs > 4 else 4
    if radius < 1:
        radius = 1

    g = EIRGraph()
    g.add_node("xy", XYToChannel("xy", width=w, height=h).as_op())

    base_dirs = {
        "e":  (1, 0),
        "w":  (-1, 0),
        "n":  (0, -1),
        "s":  (0, 1),
    }
    diag_dirs = {
        "ne": (1, -1),
        "nw": (-1, -1),
        "se": (1, 1),
        "sw": (-1, 1),
    }
    dir_map: Dict[str, tuple[int, int]] = dict(base_dirs)
    if dirs == 8:
        dir_map.update(diag_dirs)

    for name, (dx, dy) in dir_map.items():
        sdx, sdy = dx * radius, dy * radius
        shift_id = f"shift_{name}"
        delay_id = f"delay_{name}"
        flow_id = f"flow_{name}"

        g.add_node(shift_id, ShiftXY(shift_id, dx=sdx, dy=sdy, width=w, height=h).as_op())
        g.add_node(delay_id, DelayLine(delay_id, delay=delay).as_op())
        g.add_node(flow_id, EventFuse(flow_id, window=window, min_count=1).as_op())

        g.connect("xy", "ch", shift_id, "in")
        g.connect(shift_id, "out", delay_id, "in")
        g.connect("xy", "ch", flow_id, "a")
        g.connect(delay_id, "out", flow_id, "b")

    return g