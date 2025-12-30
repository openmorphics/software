"""
Determinism and Replay Contracts (v0.1)

This module implements executable checks derived from the formal TLA+ specs:
- docs/formal/tla/Types.tla
- docs/formal/tla/SALOrdering.tla
- docs/formal/tla/Merge.tla
- docs/formal/tla/ReplayEquivalence.tla
- docs/formal/tla/Determinism.tla

Functions:
- is_canonical_non_decreasing(events)
- assert_canonical_non_decreasing(events, reason="")
- pairwise_close(a, b, eps_time_us, eps_numeric_abs)
- compare_traces_equivalence(a, b, eps_time_us, eps_numeric_abs, raise_on_fail=True)

Event record shape expected by these utilities:
    {
        "ts": int,             # microseconds
        "idx": list[int],      # spatial/channel tuple (may be empty)
        "val": int | float,    # numeric payload
        "src": str,            # source identifier (optional for some checks)
        "ing": int             # ingestion order (optional for comparisons across streams)
    }

Notes:
- For comparator use we only require ts, idx, val; src/ing are optional but improve diagnostics.
- Numeric closeness uses absolute epsilon (v0.1). Relative epsilon can be added later.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple, Dict, Any, Optional


@dataclass(frozen=True)
class Divergence:
    index: int
    reason: str
    golden: Dict[str, Any] | None = None
    candidate: Dict[str, Any] | None = None
    delta_ts: Optional[int] = None
    delta_val: Optional[float] = None


def _first_idx(x: List[int]) -> int:
    return x[0] if x else -1  # empty idx sorts before any positive idx


def _idx_lex_less(a: List[int], b: List[int]) -> bool:
    # Lexicographic ascending with "shorter is less" on equal prefix
    m = min(len(a), len(b))
    for i in range(m):
        if a[i] != b[i]:
            return a[i] < b[i]
    return len(a) < len(b)


def canonical_less_than(e1: Dict[str, Any], e2: Dict[str, Any]) -> bool:
    """
    CanonicalLessThan relation as in Types.tla:
      1) ts ascending
      2) idx[0] ascending (if present)
      3) idx lexicographic ascending
      4) ingestion order ascending (ing)
    """
    t1, t2 = int(e1["ts"]), int(e2["ts"])
    if t1 != t2:
        return t1 < t2

    i1, i2 = list(e1.get("idx", [])), list(e2.get("idx", []))
    if i1 and i2 and i1[0] != i2[0]:
        return i1[0] < i2[0]

    if i1 != i2:
        return _idx_lex_less(i1, i2)

    ing1, ing2 = int(e1.get("ing", 0)), int(e2.get("ing", 0))
    if ing1 != ing2:
        return ing1 < ing2

    # Stable: treat equal as not less
    return False


def is_canonical_non_decreasing(events: Iterable[Dict[str, Any]]) -> bool:
    """
    Return True iff the sequence is sorted by the non-strict canonical order
    (never descending under canonical_less_than).
    """
    it = iter(events)
    try:
        prev = next(it)
    except StopIteration:
        return True
    for cur in it:
        if canonical_less_than(cur, prev):
            return False
        prev = cur
    return True


def _format_event(e: Dict[str, Any]) -> str:
    return f"(ts={e.get('ts')}, idx={e.get('idx')}, val={e.get('val')}, src={e.get('src')}, ing={e.get('ing')})"


def assert_canonical_non_decreasing(events: Iterable[Dict[str, Any]], reason: str = "") -> None:
    """
    Raise ValueError with a minimal counterexample if the ordering is violated.
    """
    prev = None
    for k, cur in enumerate(events):
        if prev is not None and canonical_less_than(cur, prev):
            msg = "Canonical order violation"
            if reason:
                msg += f" ({reason})"
            msg += f": out[{k-1}]={_format_event(prev)} -> out[{k}]={_format_event(cur)}"
            raise ValueError(msg)
        prev = cur


def replay_time_close(t_out: int, t_ref: int, eps_time_us: int) -> bool:
    return abs(int(t_out) - int(t_ref)) <= int(eps_time_us)


def replay_numeric_close(v_out: float, v_ref: float, eps_numeric_abs: float) -> bool:
    try:
        return abs(float(v_out) - float(v_ref)) <= float(eps_numeric_abs)
    except Exception:
        return False


def pairwise_close(
    candidate: List[Dict[str, Any]],
    golden: List[Dict[str, Any]],
    eps_time_us: int,
    eps_numeric_abs: float,
) -> Tuple[bool, Optional[Divergence]]:
    """
    1:1 pairing close check. Returns (ok, divergence).
    Divergence captures first mismatch diagnostics.
    """
    if len(candidate) != len(golden):
        return False, Divergence(index=-1, reason="count_mismatch", golden={"len": len(golden)}, candidate={"len": len(candidate)})

    for i, (c, g) in enumerate(zip(candidate, golden)):
        dt_ok = replay_time_close(c.get("ts", 0), g.get("ts", 0), eps_time_us)
        dv_ok = replay_numeric_close(c.get("val", 0.0), g.get("val", 0.0), eps_numeric_abs)
        if not (dt_ok and dv_ok):
            return (
                False,
                Divergence(
                    index=i,
                    reason="time" if not dt_ok else "numeric",
                    golden=g,
                    candidate=c,
                    delta_ts=(int(c.get("ts", 0)) - int(g.get("ts", 0))),
                    delta_val=(float(c.get("val", 0.0)) - float(g.get("val", 0.0))),
                ),
            )
    return True, None


def compare_traces_equivalence(
    candidate: List[Dict[str, Any]],
    golden: List[Dict[str, Any]],
    eps_time_us: int = 100,
    eps_numeric_abs: float = 1e-5,
    raise_on_fail: bool = True,
) -> Tuple[bool, Optional[Divergence]]:
    """
    Enforce ReplayEquivalence invariant as an executable check:
      - Canonical non-decreasing inputs
      - Equal length
      - Pairwise close within eps
    """
    assert_canonical_non_decreasing(golden, reason="golden")
    assert_canonical_non_decreasing(candidate, reason="candidate")

    ok, div = pairwise_close(candidate, golden, eps_time_us=eps_time_us, eps_numeric_abs=eps_numeric_abs)
    if not ok and raise_on_fail:
        if div and div.index >= 0:
            g = div.golden or {}
            c = div.candidate or {}
            msg = (
                f"Replay equivalence failed at index {div.index}: "
                f"cand={_format_event(c)}, gold={_format_event(g)}, "
                f"delta_ts={div.delta_ts}, delta_val={div.delta_val}, reason={div.reason}"
            )
        else:
            msg = "Replay equivalence failed: " + (div.reason if div else "unknown")
        raise AssertionError(msg)
    return ok, div