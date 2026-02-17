from __future__ import annotations
from typing import Iterable, Set, Tuple
from ..api.packet import EventPacket
from .base import CalibrationStage

class DeadPixelMask(CalibrationStage):
    def __init__(self, mask: Set[Tuple[int,int]]):
        self.mask = mask
    def apply(self, packets: Iterable[EventPacket]):
        for p in packets:
            x, y = p.meta.get("x"), p.meta.get("y")
            if (x, y) not in self.mask:
                yield p

class PolarityBalance(CalibrationStage):
    def __init__(self, gain_pos: float = 1.0, gain_neg: float = 1.0):
        self.gp, self.gn = gain_pos, gain_neg
    def apply(self, packets: Iterable[EventPacket]):
        for p in packets:
            if p.meta.get("polarity", 0) > 0:
                yield EventPacket(p.t_ns, p.channel, p.value * self.gp, p.meta)
            else:
                yield EventPacket(p.t_ns, p.channel, p.value * self.gn, p.meta)
