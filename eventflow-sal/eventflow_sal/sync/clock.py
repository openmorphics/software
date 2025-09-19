from __future__ import annotations; from dataclasses import dataclass
@dataclass class ClockModel: drift_ppm:float=0.; offset_ns:int=0; jitter_ns_p99:int=0
class ClockSync:
    def __init__(self,m:ClockModel): self.model=m
    def correct_ns(self, t:int)->int: return int(t*(1+self.model.drift_ppm/1e6))+self.model.offset_ns
