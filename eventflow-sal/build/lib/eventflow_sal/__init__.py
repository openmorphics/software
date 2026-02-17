from __future__ import annotations

from typing import Any


def open(uri: str, **kwargs: Any):
    from .open import open as _open
    return _open(uri, **kwargs)


def stream_to_jsonl(uri: str, out: str, **kwargs: Any):
    from .stream import stream_to_jsonl as _stream_to_jsonl
    return _stream_to_jsonl(uri, out, **kwargs)

__all__ = ["open", "stream_to_jsonl"]
