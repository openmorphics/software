from typing import Literal

_VALID_UNITS = {"s", "ms", "us", "ns"}

def _ensure_unit(unit: str) -> None:
    if unit not in _VALID_UNITS:
        raise ValueError(f"Unsupported time unit '{unit}'. Allowed: {sorted(_VALID_UNITS)}")

def time_scale(unit: str) -> float:
    """
    Return multiplier to seconds for the given unit.
    Example: "ms" -> 1e-3
    """
    _ensure_unit(unit)
    if unit == "s":
        return 1.0
    if unit == "ms":
        return 1e-3
    if unit == "us":
        return 1e-6
    if unit == "ns":
        return 1e-9
    # unreachable due to validation
    raise ValueError(f"Unsupported time unit '{unit}'")

def normalize_time_to(target_unit: str, value_in_unit: float, unit: str) -> float:
    """
    Convert a time value from 'unit' to 'target_unit'.
    Both units must be one of {"s","ms","us","ns"}.
    """
    _ensure_unit(unit)
    _ensure_unit(target_unit)
    seconds = value_in_unit * time_scale(unit)
    return seconds / time_scale(target_unit)