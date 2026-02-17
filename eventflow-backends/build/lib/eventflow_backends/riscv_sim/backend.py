from __future__ import annotations
from typing import Dict, Any, Optional, TYPE_CHECKING
from eventflow_backends.api import Backend, DeviceCapabilityDescriptor

if TYPE_CHECKING:
    from eventflow_core.eir.graph import EIRGraph

class RiscvSimBackend(Backend):
    def __init__(self):
        self.id = "riscv_sim"
        self.dcd = DeviceCapabilityDescriptor(
            name="RISC-V Simulator",
            vendor="EventFlow",
            profiles=["BASE","REALTIME"],
            time_resolution_ns=1_000
        )

    def compile(self, g, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {"image": None, "notes": "interpreted (prototype)"}

    def run_graph(self, g, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        from eventflow_core.runtime.exec import run_event_mode  # type: ignore
        return run_event_mode(g, inputs or {})

__all__ = ["RiscvSimBackend"]