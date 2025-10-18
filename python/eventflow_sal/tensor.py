from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple, Union, Any
import io
import json


@dataclass
class Header:
    schema_version: str = "0.1.0"
    dims: List[str] = field(default_factory=lambda: ["time", "channel", "value"])
    units: Dict[str, str] = field(default_factory=lambda: {"time": "us", "value": "dimensionless"})
    dtype: str = "f32"
    layout: str = "coo"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "dims": list(self.dims),
            "units": dict(self.units),
            "dtype": self.dtype,
            "layout": self.layout,
            "metadata": dict(self.metadata),
        }


@dataclass
class Record:
    ts: int
    idx: Tuple[int, ...]
    val: float

    def to_dict(self) -> Dict[str, Any]:
        return {"ts": int(self.ts), "idx": list(self.idx), "val": float(self.val)}


def write_event_tensor_jsonl(
    path: Union[str, Path],
    header: Dict[str, Any],
    records_iterable: Iterable[Dict[str, Any]],
) -> None:
    """
    Write Event Tensor JSONL with a header line followed by record lines.

    Header line format:
      { "header": { "schema_version": "0.1.0", "dims": ["time","channel","value"], "units": { "time": "<s|ms|us|ns>", "value": "dimensionless" }, "dtype": "f32", "layout": "coo", "metadata": { "source": "<string>", "created": "<iso8601>" } } }
    Record line format:
      { "ts": <int_time_in_unit>, "idx": [<int_channel>], "val": <float_value> }

    Notes:
    - Header is written first. No sorting is performed on records.
    - Caller is responsible for deterministic ordering of records_iterable.
    """
    p = Path(path)
    # Ensure parent exists (additive-only; create directories if missing)
    if p.parent and not p.parent.exists():
        p.parent.mkdir(parents=True, exist_ok=True)

    with p.open("w", encoding="utf-8", newline="\n") as f:
        # Header
        json.dump({"header": header}, f, separators=(",", ":"))
        f.write("\n")
        # Records
        for rec in records_iterable:
            json.dump(rec, f, separators=(",", ":"))
            f.write("\n")