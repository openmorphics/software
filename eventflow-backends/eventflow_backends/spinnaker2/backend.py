from __future__ import annotations
from typing import Dict, Any, Optional
from ..api import Backend, DeviceCapabilityDescriptor

class SpiNNaker2Backend(Backend):
    def __init__(self):
        self.id = "spinnaker2"
        self.dcd = DeviceCapabilityDescriptor(
            name="SpiNNaker2", vendor="Manchester", profiles=["BASE","REALTIME"])

    def compile(self, g, constraints: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        raise NotImplementedError("Integrate SpiNNaker2 mapping")

    def run_graph(self, g, inputs: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        raise NotImplementedError("Run on SpiNNaker2 or its simulator")
