from __future__ import annotations
from dataclasses import dataclass
from urllib.parse import urlparse, parse_qs

@dataclass(frozen=True)
class SensorURI: scheme:str; path:str; params:dict
def parse_sensor_uri(uri:str)->SensorURI:
    p=urlparse(uri); return SensorURI(f"{p.scheme}://", p.netloc+p.path, {k:v[0] for k,v in parse_qs(p.query).items()})
