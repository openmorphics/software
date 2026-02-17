from __future__ import annotations
from dataclasses import dataclass

@dataclass
class ClockModel:
    drift_ppm: float = 0.0
    offset_ns: int = 0
    jitter_ns_p99: int = 0

class ClockSync:
    """
    Minimal clock synchronization helper.
    correct_ns() applies drift and offset to a device timestamp (ns).
    """
    def __init__(self, m: ClockModel) -> None:
        self.model = m

    def correct_ns(self, t: int) -> int:
        return int(t * (1.0 + (self.model.drift_ppm / 1_000_000.0))) + self.model.offset_ns
