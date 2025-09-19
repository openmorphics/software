from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class ModelCard:
    name: str
    version: str
    task: str                      # e.g., "vision/gesture", "audio/kws"
    summary: str
    license: str
    tags: List[str] = field(default_factory=list)

@dataclass
class CapManifest:
    profiles: List[str]            # e.g., ["BASE","REALTIME"]
    min_caps: Dict[str, str]       # e.g., {"neurons": ">=1e5", "synapses": ">=1e7"}
    optional: Dict[str, str] = field(default_factory=dict)

@dataclass
class TraceMeta:
    format: str                    # "jsonl"|"parquet"|...
    epsilon_ns: int
    epsilon_val: float
