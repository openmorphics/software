from __future__ import annotations

# Keep package imports lazy so optional/experimental module trees do not break
# import of the root namespace.
_EXPORTS = {
    "vision": ".vision",
    "audio": ".audio",
    "robotics": ".robotics",
    "timeseries": ".timeseries",
    "wellness": ".wellness",
    "creative": ".creative",
    "scientific_research": ".scientific_research",
    "smart_agriculture": ".smart_agriculture",
}

__all__ = list(_EXPORTS.keys())


def __getattr__(name: str):
    if name not in _EXPORTS:
        raise AttributeError(name)
    mod = __import__(f"{__name__}{_EXPORTS[name]}", fromlist=[name])
    return mod
