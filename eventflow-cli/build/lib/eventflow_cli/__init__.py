from __future__ import annotations

from typing import List, Optional

__all__ = ["make_parser", "main"]


def make_parser():
    from .main import make_parser as _make_parser

    return _make_parser()


def main(argv: Optional[List[str]] = None):
    from .main import main as _main

    return _main(argv)
