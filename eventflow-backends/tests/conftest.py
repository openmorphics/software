from __future__ import annotations

import pytest


_MARKERS = {
    "unit": "Unit tests",
    "integration": "Integration tests",
    "conformance": "Conformance validation tests",
    "performance": "Performance tests",
    "loihi": "Loihi backend specific tests",
    "spinnaker": "SpiNNaker backend specific tests",
    "synsense": "SynSense backend specific tests",
    "discovery": "Backend discovery tests",
    "planning": "Planning and resource allocation tests",
    "execution": "Execution and simulation tests",
    "error": "Error handling tests",
}


def pytest_configure(config):
    for marker, description in _MARKERS.items():
        config.addinivalue_line("markers", f"{marker}: {description}")


def pytest_collection_modifyitems(config, items):
    for item in items:
        fspath = str(item.fspath)
        if "loihi" in fspath:
            item.add_marker(pytest.mark.loihi)
        elif "spinnaker" in fspath:
            item.add_marker(pytest.mark.spinnaker)
        elif "synsense" in fspath:
            item.add_marker(pytest.mark.synsense)
        elif "conformance" in fspath:
            item.add_marker(pytest.mark.conformance)

        name = item.name.lower()
        if "discovery" in name:
            item.add_marker(pytest.mark.discovery)
        elif "planning" in name or "plan" in name:
            item.add_marker(pytest.mark.planning)
        elif "execution" in name or "run" in name:
            item.add_marker(pytest.mark.execution)
        elif "error" in name or "fail" in name:
            item.add_marker(pytest.mark.error)
        elif "performance" in name:
            item.add_marker(pytest.mark.performance)
