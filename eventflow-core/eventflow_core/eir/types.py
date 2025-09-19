from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from ..util.units import parse_time

@dataclass
class Port:
    name: str
    shape: Optional[List[int]] = None
    meta: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OpDef:
    kind: str
    name: str
    inputs: List[Port]
    outputs: List[Port]
    params: Dict[str, Any]

def time_to_ns(v: Union[str, int]) -> int:
    return v if isinstance(v, int) else parse_time(v)
