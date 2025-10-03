from __future__ import annotations
from typing import Dict, Iterator, List
from .scheduler import build_exec_nodes
from ..eir.graph import EIRGraph
from ..eir.ops import Event

# Optional Rust acceleration
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore

def run_event_mode(g: EIRGraph, inputs: Dict[str, Iterator[Event]]) -> Dict[str, List[Event]]:
    topo, exec_nodes = g.topo(), build_exec_nodes(g)
    upstream: Dict[str, Dict[str, Iterator[Event]]] = {nid:{"in":iter([]),"pre":iter([]),"a":iter([]),"b":iter([])} for nid in g.nodes}
    for name, it in inputs.items():
        if name in upstream:
            upstream[name]["in"] = it
        else:
            upstream[name] = {"in": it}
    sinks: Dict[str,list] = {nid:[] for nid in g.nodes}; [sinks[e.src[0]].append(e.dst) for e in g.edges]
    outputs: Dict[str, List[Event]] = {nid:[] for nid in g.nodes}

    def node_iter(nid: str) -> Iterator[Event]:
        ex = exec_nodes[nid]
        if ex.kind=="fuse": return ex.fn(upstream[nid].get("a",iter([])), upstream[nid].get("b",iter([])))
        it = next((upstream[nid][p] for p in ("in","pre") if p in upstream[nid]), iter([]))
        return ex.fn(it)

    for nid in topo:
        out = list(node_iter(nid)); outputs[nid].extend(out)
        for (dst_id, dport) in sinks[nid]: upstream[dst_id][dport] = iter(out)
    return outputs

def run_fixed_dt(g: EIRGraph, inputs: Dict[str, Iterator[Event]], dt_ns: int) -> Dict[str, List[Event]]:
    """
    Execute an EIRGraph in fixed-step mode by bucketing input streams.

    Each bucket aggregates events within [k*dt, (k+1)*dt) and emits one event
    at the bucket boundary time (k+1)*dt with the aggregated value.

    Args:
        g: Parsed EIRGraph.
        inputs: Mapping of node-id to input iterators.
        dt_ns: Fixed step in nanoseconds.

    Returns:
        Dict mapping node-id to list of output events for that node.
    """
    # Prefer native bucketization if available; otherwise fall back to Python
    if _ef_native_enabled() and _ef_native is not None and hasattr(_ef_native, "bucket_sum_i64_f32"):
        import numpy as np

        def bucket(it: Iterator[Event]):
            # Collect the iterator into contiguous numpy arrays
            t_buf: List[int] = []
            v_buf: List[float] = []
            for ev in it:
                t_buf.append(int(ev[0]))
                v_buf.append(float(ev[2]))
            if not t_buf:
                return
            t_arr = np.asarray(t_buf, dtype=np.int64)
            v_arr = np.asarray(v_buf, dtype=np.float32)
            t_out, v_out = _ef_native.bucket_sum_i64_f32(t_arr, v_arr, int(dt_ns))
            # Yield aggregated events at bucket boundaries
            for t, val in zip(t_out.tolist(), v_out.tolist()):
                yield (int(t), 0, float(val), {"unit": "bucket"})
    else:
        import itertools

        def bucket(it: Iterator[Event]):
            for key, group in itertools.groupby(it, key=lambda e: (e[0] // dt_ns) * dt_ns):
                total = 0.0
                for ev in group:
                    total += ev[2]
                yield (key + dt_ns, 0, total, {"unit": "bucket"})

    return run_event_mode(g, {k: bucket(v) for k, v in inputs.items()})
