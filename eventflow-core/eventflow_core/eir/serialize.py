import json
from .graph import EIRGraph
from .ops import LIFNeuron, ExpSynapse, DelayLine, EventFuse, STFT, MelBands, XYToChannel, ShiftXY

def save(g: EIRGraph, path: str):
    obj = dict(nodes={nid: dict(kind=n.op.kind, name=n.op.name, params=n.op.params) for nid,n in g.nodes.items()},
               edges=[dict(src=e.src, dst=e.dst) for e in g.edges], metadata=g.metadata)
    with open(path, "w") as f: json.dump(obj, f, indent=2)

def load(path: str) -> EIRGraph:
    with open(path) as f: obj = json.load(f)
    g = EIRGraph(metadata=obj.get("metadata", {}))
    kinds = {
        "lif": LIFNeuron,
        "exp_syn": ExpSynapse,
        "delay": DelayLine,
        "fuse": EventFuse,
        "stft": STFT,
        "mel": MelBands,
        "xy_to_ch": XYToChannel,
        "shift_xy": ShiftXY,
    }
    for nid, nd in obj["nodes"].items():
        g.add_node(nid, kinds[nd["kind"]](nd["name"], **nd["params"]).as_op())
    for e in obj["edges"]: g.connect(e["src"][0], e["src"][1], e["dst"][0], e["dst"][1])
    return g
