from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple
from .types import OpDef, Port

@dataclass
class Node:
    op: OpDef
    id: str

@dataclass
class Edge:
    src: Tuple[str, str]
    dst: Tuple[str, str]

@dataclass
class EIRGraph:
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    name: str = ""

    def add_node(self, nid: str, op: OpDef | Dict[str, Any]):
        # Native graph API: explicit OpDef.
        if isinstance(op, OpDef):
            self.nodes[nid] = Node(op, nid)
            return nid

        # Legacy builder API: dict-shaped op description.
        if isinstance(op, dict):
            p = dict(op)
            delay = p.get("delay", "0 ms")
            self.nodes[nid] = Node(
                OpDef("delay", nid, [Port("in")], [Port("out")], {"delay": str(delay)}),
                nid,
            )
            self.metadata[f"compat:{nid}"] = repr(p)
            return nid

        raise TypeError("add_node expects OpDef or dict config")

    def add_source(self, nid: str, source: Any = None):
        """
        Compatibility helper for legacy domain modules.
        Sources are modeled as zero-delay passthrough nodes.
        """
        self.add_node(
            nid,
            OpDef("delay", nid, [Port("in")], [Port("out")], {"delay": "0 ms"}),
        )
        if source is not None:
            self.metadata[f"source:{nid}"] = repr(source)
        return nid

    def add_input(self, nid: str, source: Any = None):
        return self.add_source(nid, source)

    def add_output(self, nid: str, src: str | None = None):
        self.add_node(
            nid,
            OpDef("delay", nid, [Port("in")], [Port("out")], {"delay": "0 ms"}),
        )
        if src is not None:
            self.connect(src, nid)
        return nid

    def add_op(self, nid: str, params: Dict[str, Any] | None = None):
        """
        Compatibility helper for legacy domain modules that declare abstract ops.
        Unknown op kinds are represented as zero-delay passthrough operators.
        """
        op_name = str(nid)
        p: Dict[str, Any] = dict(params or {})
        known = {
            "lif",
            "exp_syn",
            "delay",
            "fuse",
            "stft",
            "mel",
            "xy_to_ch",
            "shift_xy",
            "bucket",
            "bucket_sum",
            "event_filter",
        }
        kind = op_name if op_name in known else "delay"

        if kind == "lif":
            p.setdefault("tau_m", "10 ms")
            p.setdefault("v_th", 1.0)
            p.setdefault("v_reset", 0.0)
            p.setdefault("r_m", 1.0)
            p.setdefault("refractory", "2 ms")
            inputs = [Port("in")]
            outputs = [Port("spike")]
        elif kind == "exp_syn":
            p.setdefault("tau_s", "5 ms")
            p.setdefault("weight", 1.0)
            inputs = [Port("pre")]
            outputs = [Port("post")]
        elif kind == "delay":
            if "delay" not in p and "delay_ns" in p:
                p["delay"] = f"{int(p['delay_ns'])} ns"
            p.setdefault("delay", "0 ms")
            inputs = [Port("in")]
            outputs = [Port("out")]
        elif kind == "fuse":
            p.setdefault("window", "50 ms")
            p.setdefault("min_count", 2)
            inputs = [Port("a"), Port("b")]
            outputs = [Port("out")]
        elif kind == "stft":
            p.setdefault("n_fft", 256)
            p.setdefault("hop", "10 ms")
            p.setdefault("sample_rate_hz", 16000)
            p.setdefault("window", "hann")
            inputs = [Port("in")]
            outputs = [Port("spec")]
        elif kind == "mel":
            p.setdefault("n_fft", 256)
            p.setdefault("n_mels", 32)
            p.setdefault("sample_rate_hz", 16000)
            p.setdefault("fmin_hz", 0.0)
            p.setdefault("fmax_hz", None)
            p.setdefault("log", True)
            inputs = [Port("in")]
            outputs = [Port("mel")]
        elif kind == "xy_to_ch":
            p.setdefault("width", 128)
            p.setdefault("height", 128)
            inputs = [Port("in")]
            outputs = [Port("ch")]
        elif kind == "shift_xy":
            p.setdefault("dx", 0)
            p.setdefault("dy", 0)
            p.setdefault("width", 128)
            p.setdefault("height", 128)
            inputs = [Port("in")]
            outputs = [Port("out")]
        elif kind == "bucket":
            p.setdefault("dt_ns", 0)
            p.setdefault("count", 1)
            inputs = [Port("in")]
            outputs = [Port("out")]
        elif kind == "bucket_sum":
            p.setdefault("buckets", 128)
            p.setdefault("window", "1 s")
            inputs = [Port("in")]
            outputs = [Port("out")]
        else:  # event_filter
            p.setdefault("min_count", 1)
            inputs = [Port("in")]
            outputs = [Port("out")]

        self.add_node(op_name, OpDef(kind, op_name, inputs, outputs, p))
        return op_name

    def connect(self, src: str, *args: str):
        if len(args) == 1:
            sport, dst, dport = "out", args[0], "in"
        elif len(args) == 3:
            sport, dst, dport = args
        else:
            raise TypeError("connect expects (src, dst) or (src, sport, dst, dport)")
        self.edges.append(Edge((str(src), str(sport)), (str(dst), str(dport))))

    def add_edge(self, src: str, dst: str):
        self.connect(src, dst)

    def enable_native_acceleration(self) -> None:
        self.metadata["native_acceleration"] = "enabled"

    def topo(self) -> List[str]:
        indeg = {nid: 0 for nid in self.nodes}; adj = {nid: [] for nid in self.nodes}
        for e in self.edges: indeg[e.dst[0]] += 1; adj[e.src[0]].append(e.dst[0])
        q = [nid for nid, d in indeg.items() if d == 0]; out = []
        while q:
            n = q.pop(); out.append(n)
            for neighbor in adj[n]:
                indeg[neighbor] -= 1
                if indeg[neighbor] == 0: q.append(neighbor)
        if len(out) != len(self.nodes): raise ValueError("cycle detected")
        return out
