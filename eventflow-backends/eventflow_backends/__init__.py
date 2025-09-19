from __future__ import annotations
from typing import Dict
from .api import Backend
from .cpu_sim.backend import CPUSimBackend
from .lava.backend import LavaBackend
from .spinnaker2.backend import SpiNNaker2Backend
from .synsense.backend import SynSenseBackend
from .brainscales.backend import BrainScaleSBackend

_REG: Dict[str, Backend] = {
    "cpu_sim": CPUSimBackend(),
    "lava": LavaBackend(),
    "spinnaker2": SpiNNaker2Backend(),
    "synsense": SynSenseBackend(),
    "brainscales": BrainScaleSBackend(),
}

def get_backend(backend_id: str) -> Backend:
    if backend_id not in _REG:
        raise KeyError(f"Unknown backend {backend_id!r}. Known: {list(_REG)}")
    return _REG[backend_id]
