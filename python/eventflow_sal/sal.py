from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, List, Tuple, Union, Dict, Any
import csv
import json
from datetime import datetime, timezone

from .units import normalize_time_to, _VALID_UNITS  # type: ignore
from .tensor import write_event_tensor_jsonl


Number = Union[int, float]


def _to_int(value: Number) -> int:
    # Round to nearest integer for time/channel where needed
    return int(round(float(value)))


def _to_float(value: Number) -> float:
    return float(value)


@dataclass
class Stream:
    """
    A deterministic in-memory stream of (time, channel, value) tuples.

    Internally stores:
      - items: List[Tuple[int, int, float]] in the provided time_unit.
      - time_unit: one of {"s","ms","us","ns"} describing the unit of 't' inside items.
    """
    items: List[Tuple[int, int, float]]
    time_unit: str = "us"

    @staticmethod
    def from_csv(
        path: Union[str, Path],
        time_col: str = "t",
        chan_col: str = "channel",
        val_col: str = "value",
        time_unit: str = "us",
    ) -> "Stream":
        """
        Load a CSV with numeric columns and return a Stream.

        Expects headers time_col, chan_col, val_col.
        Times are interpreted in 'time_unit' (must be one of {"s","ms","us","ns"}).
        Stored internally as integer time in that unit, channel as int, value as float.
        """
        if time_unit not in _VALID_UNITS:
            raise ValueError(f"Unsupported time_unit '{time_unit}'. Allowed: {sorted(_VALID_UNITS)}")

        p = Path(path)
        items: List[Tuple[int, int, float]] = []
        with p.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            missing = [c for c in (time_col, chan_col, val_col) if c not in (reader.fieldnames or [])]
            if missing:
                raise ValueError(f"CSV missing required columns: {missing}")

            for row in reader:
                try:
                    t_raw = float(row[time_col])
                    c_raw = float(row[chan_col])
                    v_raw = float(row[val_col])
                except Exception as e:
                    raise ValueError(f"Non-numeric row encountered: {row}") from e

                t_int = _to_int(t_raw)
                c_int = _to_int(c_raw)
                v_f = _to_float(v_raw)

                items.append((t_int, c_int, v_f))

        return Stream(items=items, time_unit=time_unit)

    def _event_records(self, target_time_unit: str = "us") -> Iterator[Dict[str, Any]]:
        if target_time_unit not in _VALID_UNITS:
            raise ValueError(f"Unsupported target_time_unit '{target_time_unit}'. Allowed: {sorted(_VALID_UNITS)}")

        for t_int, chan, val in self.items:
            # Convert time to target unit and emit integer timestamp
            t_conv = normalize_time_to(target_time_unit, float(t_int), self.time_unit)
            yield {
                "ts": int(round(t_conv)),
                "idx": [int(chan)],
                "val": float(val),
            }

    def to_event_tensor(
        self,
        target_time_unit: str = "us",
        source_name: str = "csv",
    ) -> Tuple[Dict[str, Any], Iterable[Dict[str, Any]]]:
        """
        Build header dict and an iterable of record dicts suitable for write_event_tensor_jsonl.
        """
        if target_time_unit not in _VALID_UNITS:
            raise ValueError(f"Unsupported target_time_unit '{target_time_unit}'. Allowed: {sorted(_VALID_UNITS)}")

        created_iso = datetime.now(timezone.utc).isoformat()
        header = {
            "schema_version": "0.1.0",
            "dims": ["time", "channel", "value"],
            "units": {"time": target_time_unit, "value": "dimensionless"},
            "dtype": "f32",
            "layout": "coo",
            "metadata": {"source": str(source_name), "created": created_iso},
        }
        return header, self._event_records(target_time_unit=target_time_unit)

    def dump_jsonl(
        self,
        out_path: Union[str, Path],
        target_time_unit: str = "us",
        source_name: str = "csv",
    ) -> None:
        """
        Write an Event Tensor JSONL file to out_path with the specified target_time_unit and source metadata.
        """
        header, records = self.to_event_tensor(target_time_unit=target_time_unit, source_name=source_name)
        write_event_tensor_jsonl(out_path, header=header, records_iterable=records)