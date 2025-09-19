from .graph import EIRGraph; from .types import time_to_ns
def validate(g: EIRGraph): g.topo(); [time_to_ns(v) for n in g.nodes.values() for v in n.op.params.values() if isinstance(v,str) and "s" in v]
