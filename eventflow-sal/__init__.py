"""
EventFlow SAL convenience re-exports.

This top-level module provides thin wrappers over the canonical package 'eventflow_sal'.
Prefer importing 'eventflow_sal' directly in application code.
"""
from __future__ import annotations
import logging
from typing import Iterator, Optional, Any
from eventflow_sal.open import open as _open  # type: ignore[attr-defined]

__all__ = ["open", "close", "read"]

_log = logging.getLogger(__name__)

def open(uri: str, **kwargs):
    """
    Open a SAL source via URI. Delegates to eventflow_sal.open.open().
    """
    return _open(uri, **kwargs)

def read(source, n: Optional[int] = None, duration: Optional[int] = None) -> Iterator[Any]:
    """
    Minimal read helper for sources that expose subscribe().
    - If n is provided, yields up to n EventPacket records from source.subscribe().
    - duration is reserved for future time-window reads and currently ignored.
    """
    sub = getattr(source, "subscribe", None)
    if not callable(sub):
        raise ValueError("sal.invalid_source: object does not provide subscribe()")
    count = 0
    for pkt in sub():
        yield pkt
        count += 1
        if n is not None and count >= n:
            break

def close(source) -> None:
    """
    Close a SAL source if it provides close(); otherwise no-op.
    """
    try:
        close_fn = getattr(source, "close", None)
        if callable(close_fn):
            close_fn()
    except Exception as e:
        _log.warning(f"sal.close failed on source {type(source).__name__}: {e}")
