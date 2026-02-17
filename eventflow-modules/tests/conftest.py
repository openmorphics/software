"""Test fixtures for eventflow-modules."""

from __future__ import annotations

import pytest


try:
    import pytest_benchmark  # type: ignore  # noqa: F401
except Exception:
    @pytest.fixture
    def benchmark():
        """Minimal fallback benchmark fixture when pytest-benchmark is unavailable."""

        def _run(func, *args, **kwargs):
            return func(*args, **kwargs)

        return _run
