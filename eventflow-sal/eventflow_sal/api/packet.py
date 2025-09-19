from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Literal

TimeUnit = Literal["ns","us","ms"]
MagUnit = str

@dataclass(frozen=True)
class EventPacket:
    t_ns: int; channel: int; value: float; meta: Dict[str,Any]
    def with_time_offset(self,d:int)->"EventPacket": return EventPacket(self.t_ns+d,self.channel,self.value,self.meta)

def dvs_event(t,x,y,p)->EventPacket: return EventPacket(t,0,float(p),{"unit":"pol","x":x,"y":y,"polarity":p})
def audio_band_event(t,b,m,u:MagUnit="dB")->EventPacket: return EventPacket(t,b,m,{"unit":u})
def imu_axis_event(t,a,m,u:MagUnit="m/s^2")->EventPacket: return EventPacket(t,a,m,{"unit":u})
