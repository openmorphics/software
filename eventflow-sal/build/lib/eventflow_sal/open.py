from __future__ import annotations
from .registry import resolve_source
from .api.uri import parse_sensor_uri

def open(uri: str, **overrides):
    u = parse_sensor_uri(uri); return resolve_source(u, overrides)
