from __future__ import annotations

"""
EventFlow Core SDK (stubs)
"""
from typing import Optional, Dict, Any

__all__ = ["version", "compile_and_run"]

def version() -> str:
    return "0.1.0"

def compile_and_run(graph: Any, backend: str = "auto", constraints: Optional[Dict[str, Any]] = None) -> None:
    """
    Compile and execute an EIR graph on the selected backend (stub).
    """
    raise NotImplementedError("EventFlow core runtime not implemented yet.")
