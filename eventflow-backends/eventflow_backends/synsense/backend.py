from __future__ import annotations
from typing import Dict, Any, Optional
from ..api import Backend, DeviceCapabilityDescriptor

class SynSenseBackend(Backend):
    def __init__(self):
        self.id = "synsense"
        self.dcd = DeviceCapabilityDescriptor(
            name="SynSense Device", vendor="SynSense", profiles=["BASE","REALTIME"])

    def compile(self, g, constraints: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        raise NotImplementedError("Integrate SynSense mapping")

    def run_graph(self, g, inputs: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        raise NotImplementedError("Run on SynSense hardware")
