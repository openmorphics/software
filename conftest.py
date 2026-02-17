"""Root test bootstrap for monorepo package imports."""

from __future__ import annotations

import os
import sys

import pytest

_ROOT = os.path.abspath(os.path.dirname(__file__))
_PKG_DIRS = (
    "eventflow-backends",
    "eventflow-cli",
    "eventflow-core",
    "eventflow-hub",
    "eventflow-modules",
    "eventflow-sal",
)

for rel in _PKG_DIRS:
    path = os.path.join(_ROOT, rel)
    if os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)


try:
    import pytest_benchmark  # type: ignore  # noqa: F401
except Exception:
    @pytest.fixture
    def benchmark():
        """Fallback benchmark fixture when pytest-benchmark is unavailable."""

        def _run(func, *args, **kwargs):
            return func(*args, **kwargs)

        return _run
