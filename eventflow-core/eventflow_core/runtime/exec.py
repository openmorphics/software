from __future__ import annotations
from typing import Dict, Iterator, List
from .scheduler import build_exec_nodes
from ..eir.graph import EIRGraph
from ..eir.ops import Event

def run_event_mode(g: EIRGraph, inputs: Dict[str, Iterator[Event]]) -> Dict[str, List[Event]]:
    topo, exec_nodes = g.topo(), build_exec_nodes(g)
    upstream: Dict[str, Dict[str, Iterator[Event]]] = {nid:{"in":iter([]),"pre":iter([]),"a":iter([]),"b":iter([])} for nid in g.nodes}
    for name,it in inputs.items(): upstream[name]={"in":it}
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
    import itertools
    def bucket(it:Iterator[Event]):
        for key, bucket in itertools.groupby(it, key=lambda e: (e[0]//dt_ns)*dt_ns):
            yield (key+dt_ns, 0, sum(ev[2] for ev in bucket), {"unit":"bucket"})
    return run_event_mode(g, {k: bucket(v) for k,v in inputs.items()})
