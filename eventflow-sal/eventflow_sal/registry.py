from __future__ import annotations
from typing import Dict, Callable
from .api.uri import SensorURI; from .api.source import BaseSource
from .drivers.dvs import DVSSource, AEDAT4FileSource
from .drivers.audio import MicSource, WAVFileSource
from .drivers.imu import IMUSource, CSVFileSource

_REGISTRY: Dict[str, Callable[[SensorURI, dict], BaseSource]] = {
    "vision.dvs://": lambda u,kw: AEDAT4FileSource(u.path,**kw) if u.path.endswith(".aedat4") else DVSSource(device=u.path,**kw),
    "audio.mic://": lambda u,kw: WAVFileSource(u.path,**kw) if u.path.endswith(".wav") else MicSource(device=u.path,**kw),
    "imu.6dof://": lambda u,kw: CSVFileSource(u.path,**kw) if u.path.endswith(".csv") else IMUSource(device=u.path,**kw),
    "file://": lambda u,kw: AEDAT4FileSource(u.path,**kw),
}
def resolve_source(u: SensorURI, overrides: dict) -> BaseSource:
    if u.scheme not in _REGISTRY: raise ValueError(f"No driver for {u.scheme}")
    return _REGISTRY[u.scheme](u, overrides)
