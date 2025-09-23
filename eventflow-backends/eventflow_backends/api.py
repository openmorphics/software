from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional

# Avoid importing eventflow_core at module import time to keep this package lightweight.

@dataclass
class DeviceCapabilityDescriptor:
    name: str
    vendor: str
    profiles: list                 # ["BASE","REALTIME","LEARNING","LOWPOWER"]
    max_neurons: Optional[int] = None
    max_synapses: Optional[int] = None
    time_resolution_ns: Optional[int] = None
    features: Dict[str, Any] | None = None

class Backend:
    """
    Minimal backend interface. Backends may optionally implement compile()
    to emit device images; run_graph() must return node→events map (for CLI).
    """
    id: str
    dcd: DeviceCapabilityDescriptor

    def compile(self, g, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:  # g: EIRGraph
        """
        Optional: Compile an EIR graph to a backend-specific binary image or configuration.
        This method is responsible for mapping the abstract graph to concrete hardware resources.
        Returns a JSON-serializable dictionary representing the compiled artifact.
        """
        raise NotImplementedError("Backend must implement the 'compile' method.")

    def run_graph(self, g, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a compiled or interpreted EIR graph with the provided input event streams.
        Args:
            g: The EIRGraph instance.
            inputs: A dictionary mapping input node IDs to event iterators.
        Returns:
            A dictionary mapping output node IDs to lists of events produced.
        """
        raise NotImplementedError("Backend must implement the 'run_graph' method.")
