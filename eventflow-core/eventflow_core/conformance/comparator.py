"""
EventFlow Conformance — Trace Equivalence Comparator v0.1

Compares two Event Tensor JSONL traces (golden vs candidate) for equivalence under
epsilon tolerances as defined in docs/DETERMINISM.md.

API:
- compare_traces_jsonl(golden_path, candidate_path, eps_time_us=100, eps_numeric=1e-5) -> dict
- print_report(result: dict) -> None
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class TraceHeader:
    schema_version: str
    dims: List[str]
    time_unit: str
    value_unit: str
    metadata: Dict[str, Any]


def _read_header(fh) -> TraceHeader:
    line = fh.readline()
    if not line:
        raise ValueError("empty trace")
    obj = json.loads(line)
    if "header" not in obj:
        raise ValueError("first line must be a header object with key 'header'")
    h = obj["header"]
    units = h.get("units", {})
    return TraceHeader(
        schema_version=str(h.get("schema_version", "")),
        dims=list(h.get("dims", [])),
        time_unit=str(units.get("time", "us")),
        value_unit=str(units.get("value", "dimensionless")),
        metadata=dict(h.get("metadata", {})),
    )


def _read_records(fh) -> List[Tuple[int, List[int], float]]:
    out: List[Tuple[int, List[int], float]] = []
    for line in fh:
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        ts = int(rec["ts"])
        idx = [int(i) for i in rec["idx"]]
        val = float(rec.get("val", 0.0))
        out.append((ts, idx, val))
    return out


def compare_traces_jsonl(
    golden_path: str,
    candidate_path: str,
    eps_time_us: int = 100,
    eps_numeric: float = 1e-5,
) -> Dict[str, Any]:
    """
    Compare two JSONL traces 1:1 in order. Assumes both traces are sorted per canonical ordering.
    Returns a dict with summary and mismatches (up to a cap).
    """
    result: Dict[str, Any] = {
        "ok": True,
        "golden": golden_path,
        "candidate": candidate_path,
        "eps_time_us": eps_time_us,
        "eps_numeric": eps_numeric,
        "mismatch_count": 0,
        "first_mismatches": [],  # up to 20 entries
        "summary": {},
    }

    with open(golden_path, "r", encoding="utf-8") as fg, open(candidate_path, "r", encoding="utf-8") as fc:
        hg = _read_header(fg)
        hc = _read_header(fc)

        # Basic header compatibility (time unit)
        if hg.time_unit != hc.time_unit:
            result["ok"] = False
            result["first_mismatches"].append({
                "kind": "header",
                "field": "units.time",
                "golden": hg.time_unit,
                "candidate": hc.time_unit,
            })

        rg = _read_records(fg)
        rc = _read_records(fc)

    # Count mismatch
    if len(rg) != len(rc):
        result["ok"] = False
        result["summary"]["count_golden"] = len(rg)
        result["summary"]["count_candidate"] = len(rc)

    # Element-wise comparison up to min length
    mismatches = 0
    firsts: List[Dict[str, Any]] = []
    n = min(len(rg), len(rc))
    for i in range(n):
        tsg, idxg, valg = rg[i]
        tsc, idxc, valc = rc[i]
        # Timing delta (absolute)
        dt = abs(tsc - tsg)
        # Numeric relative error
        denom = max(1.0, abs(valg))
        dv = abs(valc - valg) / denom
        idx_equal = (idxg == idxc)
        if (dt > eps_time_us) or (dv > eps_numeric) or (not idx_equal):
            mismatches += 1
            if len(firsts) < 20:
                firsts.append({
                    "i": i,
                    "ts_golden": tsg,
                    "ts_candidate": tsc,
                    "dt_us": dt,
                    "idx_golden": idxg,
                    "idx_candidate": idxc,
                    "val_golden": valg,
                    "val_candidate": valc,
                    "rel_err": dv,
                })

    if mismatches > 0:
        result["ok"] = False
        result["mismatch_count"] = mismatches
        result["first_mismatches"] = firsts

    # Summaries
    result["summary"].setdefault("count_golden", len(rg))
    result["summary"].setdefault("count_candidate", len(rc))
    return result


def print_report(result: Dict[str, Any]) -> None:
    ok = result.get("ok", False)
    if ok:
        print("Trace equivalence: OK")
    else:
        print("Trace equivalence: FAIL")
    print(f"golden   : {result.get('golden')}")
    print(f"candidate: {result.get('candidate')}")
    print(f"eps_time_us={result.get('eps_time_us')} eps_numeric={result.get('eps_numeric')}")
    summary = result.get("summary", {})
    print(f"counts   : golden={summary.get('count_golden')} candidate={summary.get('count_candidate')}")
    mm = result.get("mismatch_count", 0)
    print(f"mismatches: {mm}")
    if not ok and result.get("first_mismatches"):
        print("first mismatches:")
        for m in result["first_mismatches"]:
            print(" -", m)