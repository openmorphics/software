from __future__ import annotations
from dataclasses import dataclass

_NS = {"ns":1, "us":1_000, "ms":1_000_000, "s":1_000_000_000}

def to_ns(value: float, unit: str) -> int:
    if unit not in _NS: raise ValueError(f"Unknown unit {unit}")
    return int(round(value * _NS[unit]))

def parse_time(s: str) -> int:
    s = s.strip().lower()
    for u in ["ns","us","ms","s"]:
        if s.endswith(f" {u}") or s.endswith(u):
            v = float(s.replace(u,"").strip())
            return to_ns(v, u)
    raise ValueError(f"Bad time literal: {s}")
