"""
Pytest Configuration for EventFlow Backends Testing

This module provides pytest configuration and utilities for comprehensive
testing of vendor backends.
"""

import pytest
from typing import Dict, Any


# Test configuration
TEST_CONFIG = {
    "markers": {
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
        "error": "Error handling tests"
    },
    "coverage": {
        "source": ["eventflow_backends"],
        "report": ["term-missing", "html"],
        "fail_under": 80
    }
}


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Test configuration fixture."""
    return TEST_CONFIG


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Setup test environment for each test."""
    # Reset any global state that might persist between tests
    # This ensures test isolation
    yield
    # Cleanup after test


def pytest_configure(config):
    """Configure pytest with custom markers."""
    for marker, description in TEST_CONFIG["markers"].items():
        config.addinivalue_line("markers", f"{marker}: {description}")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test path."""
    for item in items:
        # Add markers based on test file path
        if "loihi" in str(item.fspath):
            item.add_marker(pytest.mark.loihi)
        elif "spinnaker" in str(item.fspath):
            item.add_marker(pytest.mark.spinnaker)
        elif "synsense" in str(item.fspath):
            item.add_marker(pytest.mark.synsense)
        elif "conformance" in str(item.fspath):
            item.add_marker(pytest.mark.conformance)

        # Add category markers based on test name
        test_name = item.name.lower()
        if "discovery" in test_name:
            item.add_marker(pytest.mark.discovery)
        elif "planning" in test_name or "plan" in test_name:
            item.add_marker(pytest.mark.planning)
        elif "execution" in test_name or "run" in test_name:
            item.add_marker(pytest.mark.execution)
        elif "error" in test_name or "fail" in test_name:
            item.add_marker(pytest.mark.error)
        elif "performance" in test_name:
            item.add_marker(pytest.mark.performance)