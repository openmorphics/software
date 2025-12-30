"""
Conformance Validation Tests

Tests backend conformance against EventFlow standards and cross-backend compatibility.
Validates that all vendor backends produce equivalent results for the same workloads.
"""

import pytest
import json
import tempfile
import os
from typing import Dict, Any, List
from unittest.mock import patch
from eventflow_backends.vendor_backends.loihi.backend import LoihiBackend
from eventflow_backends.vendor_backends.spinnaker.backend import SpiNNakerBackend
from eventflow_backends.vendor_backends.synsense.backend import SynSenseBackend


class TestConformanceValidation:
    """Conformance validation test suite."""

    @pytest.fixture
    def all_backends(self):
        """All vendor backends for cross-validation."""
        return {
            "loihi": LoihiBackend(),
            "spinnaker": SpiNNakerBackend(),
            "synsense": SynSenseBackend()
        }

    @pytest.fixture
    def reference_eir(self):
        """Reference EIR that all backends should be able to handle."""
        return {
            "profile": "REALTIME",
            "graph": {"name": "conformance_test"},
            "nodes": [
                {"id": "input", "kind": "input", "op": "input_spikes"},
                {"id": "lif", "kind": "spiking_neuron", "op": "lif", "params": {"tau": 10.0}},
                {"id": "synapse", "kind": "synapse", "op": "synapse_exp", "params": {"weight": 1.0}},
                {"id": "output", "kind": "output", "op": "output_spikes"},
            ],
            "edges": [
                {"from": "input", "to": "lif"},
                {"from": "lif", "to": "synapse"},
                {"from": "synapse", "to": "output"},
            ],
            "seed": 42
        }

    @pytest.fixture
    def mock_all_sdks(self):
        """Mock all SDKs as available for testing."""
        with patch('eventflow_backends.vendor_backends.loihi.backend._check_nxsdk', return_value=True), \
             patch('eventflow_backends.vendor_backends.spinnaker.backend._check_spynnaker', return_value=True), \
             patch('eventflow_backends.vendor_backends.synsense.backend._check_synsense', return_value=True):
            yield

    def test_conformance_profile_compatibility(self, all_backends):
        """Test all backends support the same conformance profiles."""
        profiles_by_backend = {}

        for name, backend in all_backends.items():
            dcd = backend.dcd()
            profiles = set(dcd.get("conformance_profiles", []))
            profiles_by_backend[name] = profiles

        # All backends should support REALTIME profile
        for name, profiles in profiles_by_backend.items():
            assert "REALTIME" in profiles, f"{name} missing REALTIME profile support"

        # Check for profile consistency (all should have same core profiles)
        common_profiles = set.intersection(*profiles_by_backend.values())
        assert "REALTIME" in common_profiles

    def test_opset_intersection(self, all_backends):
        """Test common opset across all backends."""
        opsets = {}
        for name, backend in all_backends.items():
            dcd = backend.dcd()
            opsets[name] = set(dcd.get("supported_ops", []))

        # Find common ops
        common_ops = set.intersection(*opsets.values())

        # Core ops that should be supported by all backends
        expected_common_ops = {"lif", "synapse_exp"}
        assert expected_common_ops.issubset(common_ops), f"Missing common ops: {expected_common_ops - common_ops}"

        # Each backend should have some unique ops
        for name, opset in opsets.items():
            unique_ops = opset - common_ops
            assert len(unique_ops) > 0, f"{name} has no unique operations"

    def test_capability_ranges(self, all_backends):
        """Test capability ranges are reasonable and distinct."""
        capabilities = {}

        for name, backend in all_backends.items():
            dcd = backend.dcd()
            limits = dcd.get("limits", {})
            power = dcd.get("power", {})

            capabilities[name] = {
                "max_neurons": limits.get("max_neurons", 0),
                "power_efficiency": power.get("mw_per_spike_typ", float('inf')),
                "time_resolution": dcd.get("time_resolution_ns", float('inf'))
            }

        # SynSense should be most power efficient
        synsense_eff = capabilities["synsense"]["power_efficiency"]
        assert all(synsense_eff <= cap["power_efficiency"] for cap in capabilities.values())

        # SpiNNaker should support most neurons
        spinnaker_neurons = capabilities["spinnaker"]["max_neurons"]
        assert all(spinnaker_neurons >= cap["max_neurons"] for cap in capabilities.values())

        # SynSense should have highest time resolution
        synsense_res = capabilities["synsense"]["time_resolution"]
        assert all(synsense_res <= cap["time_resolution"] for cap in capabilities.values())

    def test_deterministic_planning(self, all_backends, reference_eir, mock_all_sdks):
        """Test that planning is deterministic for same inputs."""
        plans_by_backend = {}

        for name, backend in all_backends.items():
            # Plan multiple times with same input
            plans = []
            for _ in range(3):
                plan = backend.plan(reference_eir)
                plans.append(json.dumps(plan, sort_keys=True))

            # All plans should be identical
            assert all(p == plans[0] for p in plans), f"{name} planning not deterministic"

            plans_by_backend[name] = plan

        # Plans should have consistent structure across backends
        for name, plan in plans_by_backend.items():
            assert "backend" in plan
            assert "graph" in plan
            assert "partitions" in plan
            assert plan["backend"]["name"] == name

    def test_plan_structure_consistency(self, all_backends, reference_eir, mock_all_sdks):
        """Test plan structures are consistent across backends."""
        plans = {}
        for name, backend in all_backends.items():
            plans[name] = backend.plan(reference_eir)

        # All plans should have same graph info
        graph_info = plans["loihi"]["graph"]
        for name, plan in plans.items():
            assert plan["graph"]["name"] == graph_info["name"]
            assert plan["graph"]["profile"] == graph_info["profile"]
            assert plan["graph"]["seed"] == graph_info["seed"]

    def test_error_handling_consistency(self, all_backends):
        """Test error handling is consistent across backends."""
        invalid_eir = {"profile": "INVALID"}

        for name, backend in all_backends.items():
            with pytest.raises((ValueError, RuntimeError)):
                backend.plan(invalid_eir)

    def test_backend_isolation(self, all_backends, reference_eir, mock_all_sdks):
        """Test backends don't interfere with each other."""
        # Plan with all backends in sequence
        results = {}
        for name, backend in all_backends.items():
            results[name] = backend.plan(reference_eir)

        # Verify each backend produced its own plan
        for name, plan in results.items():
            assert plan["backend"]["name"] == name

    def test_conformance_validation_utility(self, all_backends):
        """Test conformance validation utility functions."""
        from eventflow_backends.vendor_backends.loihi.backend import _check_nxsdk
        from eventflow_backends.vendor_backends.spinnaker.backend import _check_spynnaker
        from eventflow_backends.vendor_backends.synsense.backend import _check_synsense

        # Test SDK check functions exist and are callable
        assert callable(_check_nxsdk)
        assert callable(_check_spynnaker)
        assert callable(_check_synsense)

        # Without mocking, these should return False (SDKs not installed)
        # but the functions should not raise exceptions
        try:
            loihi_available = _check_nxsdk()
            spinnaker_available = _check_spynnaker()
            synsense_available = _check_synsense()

            # These should be boolean values
            assert isinstance(loihi_available, bool)
            assert isinstance(spinnaker_available, bool)
            assert isinstance(synsense_available, bool)

        except Exception as e:
            pytest.fail(f"SDK check functions should not raise exceptions: {e}")

    def test_dcd_schema_compliance(self, all_backends):
        """Test DCD files comply with expected schema."""
        required_dcd_fields = [
            "name", "vendor", "version", "conformance_profiles",
            "supported_ops", "time_resolution_ns", "limits", "power"
        ]

        for name, backend in all_backends.items():
            dcd = backend.dcd()

            for field in required_dcd_fields:
                assert field in dcd, f"{name} DCD missing required field: {field}"

            # Validate limits structure
            limits = dcd["limits"]
            assert "max_neurons" in limits
            assert "max_synapses" in limits

            # Validate power structure
            power = dcd["power"]
            assert "mw_per_spike_typ" in power
            assert "idle_mw" in power

    def test_opset_version_consistency(self, all_backends):
        """Test opset versions are properly specified."""
        for name, backend in all_backends.items():
            dcd = backend.dcd()
            supported_ops = dcd.get("supported_ops", [])
            opset_versions = dcd.get("opset_versions", {})

            for op in supported_ops:
                assert op in opset_versions, f"{name} missing version for op: {op}"

                version = opset_versions[op]
                assert isinstance(version, str), f"{name} {op} version should be string"
                # Basic semantic version check
                parts = version.split(".")
                assert len(parts) >= 2, f"{name} {op} invalid version format: {version}"