from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from .types import OpDef

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

    def add_node(self, nid: str, op: OpDef): self.nodes[nid] = Node(op, nid)
    def connect(self, src: str, sport: str, dst: str, dport: str): self.edges.append(Edge((src, sport), (dst, dport)))

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
