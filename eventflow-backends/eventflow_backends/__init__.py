from __future__ import annotations
from typing import Dict
from .api import Backend
from .cpu_sim.backend import CPUSimBackend

"""
Minimal in-process backend registry.

Note:
- Vendor backends (lava/loihi, spinnaker2, synsense, brainscales) are available as stubs in this repo
  but are not registered here to avoid import-time side effects and NotImplementedError placeholders.
- Use the dynamic registry (eventflow-backends/registry/registry.py) for planning/execution workflows.
"""

_REG: Dict[str, Backend] = {
    "cpu_sim": CPUSimBackend(),
    "cpu-sim": CPUSimBackend(),  # alias for hyphenated id
}

def get_backend(backend_id: str) -> Backend:
    if backend_id not in _REG:
        raise KeyError(f"Unknown backend {backend_id!r}. Known: {list(_REG)}")
    return _REG[backend_id]
