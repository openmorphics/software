from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class DeviceCapabilityDescriptor:
    vendor:str; model:str; kind:str; channels:int; time_resolution_ns:int
    dynamic_range_db:Optional[float]=None; jitter_ns_p99:Optional[int]=None
    drift_ppm:Optional[float]=None; extras:Optional[Dict[str,Any]]=None
    def to_json(self)->Dict[str,Any]: return self.__dict__

def validate_dcd(d:Dict[str,Any]):
    if missing:=[k for k in ["vendor","model","kind","channels","time_resolution_ns"] if k not in d]:
        raise ValueError(f"Missing DCD fields: {missing}")
