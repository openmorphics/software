from __future__ import annotations
from typing import Dict, Any, Optional, TYPE_CHECKING, Iterable, Tuple
from ..api import Backend, DeviceCapabilityDescriptor

if TYPE_CHECKING:
    # type-only import to avoid runtime dependency
    from eventflow_core.eir.graph import EIRGraph

def _default_inputs(g) -> Dict[str, Iterable[Tuple[int,int,float,dict]]]:
    def stim():
        for i in range(3):
            yield (1_000_000*(i+1), 0, 1.0, {"unit":"stim"})
    return {nid: stim() for nid in getattr(g, "nodes", {})}

class CPUSimBackend(Backend):
    def __init__(self):
        self.id = "cpu_sim"
        self.dcd = DeviceCapabilityDescriptor(
            name="CPU Simulator", vendor="EventFlow",
            profiles=["BASE","REALTIME"], time_resolution_ns=1_000)

    def compile(self, g, constraints: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        return {"image": None, "notes": "interpreted"}

    def run_graph(self, g, inputs: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        # Import inside method to avoid hard dependency when not used
        from eventflow_core.runtime.exec import run_event_mode  # type: ignore
        return run_event_mode(g, inputs or _default_inputs(g))
