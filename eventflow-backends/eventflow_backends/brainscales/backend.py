from __future__ import annotations
from typing import Dict, Any, Optional
from ..api import Backend, DeviceCapabilityDescriptor

class BrainScaleSBackend(Backend):
    def __init__(self):
        self.id = "brainscales"
        self.dcd = DeviceCapabilityDescriptor(
            name="BrainScaleS", vendor="Heidelberg", profiles=["BASE","REALTIME"])

    def compile(self, g, constraints: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        raise NotImplementedError("Integrate BrainScaleS mapping")

    def run_graph(self, g, inputs: Optional[Dict[str, Any]]=None) -> Dict[str, Any]:
        raise NotImplementedError("Run on BrainScaleS hardware")
