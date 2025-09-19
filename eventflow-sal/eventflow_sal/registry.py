from __future__ import annotations
from typing import Dict
from .api.uri import SensorURI
from .api.source import BaseSource
from .drivers.dvs import DVSSource, AEDAT4FileSource
from .drivers.audio import MicSource, WAVFileSource
from .drivers.imu import IMUSource, CSVFileSource


def _effective_path(u: SensorURI) -> str:
    """
    Use query param ?path= if provided (compat with URIs like audio.mic://file?path=...),
    otherwise fall back to netloc+path parsed into SensorURI.path.
    """
    params = getattr(u, "params", {}) or {}
    return params.get("path") or u.path


def resolve_source(u: SensorURI, overrides: dict) -> BaseSource:
    """
    Registry dispatcher that supports both device URIs and file-based URIs
    with ?path= compatibility across schemes.
    """
    kind = u.scheme
    path = _effective_path(u) or ""

    if kind == "vision.dvs://":
        # File-based DVS recording
        if path.lower().endswith(".aedat4"):
            return AEDAT4FileSource(path, **overrides)
        # JSONL is handled by SAL stream normalization path (api.stream_to_jsonl passthrough),
        # but if someone calls open() directly with a JSONL we fail fast:
        if path.lower().endswith(".jsonl"):
            raise ValueError("sal.unsupported_source: JSONL normalization must use SAL stream_to_jsonl(), not open()")
        # Device-based DVS (live camera or stub)
        return DVSSource(device=path or "default", **overrides)

    if kind == "audio.mic://":
        # WAV file → band stream
        if path.lower().endswith(".wav"):
            # Map overrides: b=bands, hop=ns (already provided by caller)
            b = int(overrides.get("b", 32))
            hop = int(overrides.get("hop", 10_000_000))  # default 10 ms in ns
            return WAVFileSource(path, b=b, hop=hop)
        # Device microphone (stub)
        return MicSource(device=path or "default", **overrides)

    if kind == "imu.6dof://":
        if path.lower().endswith(".csv"):
            return CSVFileSource(path, **overrides)
        return IMUSource(device=path or "default", **overrides)

    if kind == "file://":
        # Generic file scheme: route by extension (AEDAT4 for DVS)
        if path.lower().endswith(".aedat4"):
            return AEDAT4FileSource(path, **overrides)
        raise ValueError(f"file:// scheme unsupported for path: {path!r}")

    raise ValueError(f"sal.unsupported_source: no driver for scheme {kind!r}")
