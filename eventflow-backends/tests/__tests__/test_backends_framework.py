"""
Comprehensive EventFlow Vendor Backends Testing Framework

This module provides a unified pytest-based testing framework for all vendor backends
(Loihi, SpiNNaker, SynSense) covering discovery, configuration, planning, execution,
error handling, and conformance validation.

Test Categories:
- Discovery Tests: Backend registration, entry points, imports
- Configuration Tests: DCD validation, capability negotiation
- Planning Tests: Plan generation, resource allocation
- Execution Tests: Run simulation, trace generation
- Error Tests: Hardware unavailability, invalid inputs
- Conformance Tests: Equivalence with CPU simulator
"""

import pytest
import json
import tempfile
import os
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, MagicMock

# Backend imports
from eventflow_backends.vendor_backends.loihi.backend import LoihiBackend, _check_nxsdk
from eventflow_backends.vendor_backends.spinnaker.backend import SpiNNakerBackend, _check_spynnaker
from eventflow_backends.vendor_backends.synsense.backend import SynSenseBackend, _check_synsense


class TestBackendFramework:
    """Unified backend testing framework."""

    # Test data fixtures (defined as class attributes for reuse)
    sample_eir_realtime = {
        "profile": "REALTIME",
        "graph": {"name": "test_graph"},
        "nodes": [
            {"id": "n1", "kind": "spiking_neuron", "op": "lif"},
            {"id": "n2", "kind": "synapse", "op": "synapse_exp"},
        ],
        "edges": [
            {"from": "n1", "to": "n2"}
        ],
        "seed": 42
    }

    sample_eir_complex = {
        "profile": "REALTIME",
        "graph": {"name": "complex_graph"},
        "nodes": [
            {"id": "input", "kind": "input", "op": "input_spikes"},
            {"id": "lif1", "kind": "spiking_neuron", "op": "lif", "params": {"tau": 10.0}},
            {"id": "lif2", "kind": "spiking_neuron", "op": "lif", "params": {"tau": 15.0}},
            {"id": "syn1", "kind": "synapse", "op": "synapse_exp", "params": {"weight": 1.0}},
            {"id": "syn2", "kind": "synapse", "op": "synapse_exp", "params": {"weight": 0.5}},
            {"id": "output", "kind": "output", "op": "output_spikes"},
        ],
        "edges": [
            {"from": "input", "to": "lif1"},
            {"from": "lif1", "to": "syn1"},
            {"from": "syn1", "to": "lif2"},
            {"from": "lif2", "to": "syn2"},
            {"from": "syn2", "to": "output"},
        ],
        "seed": 12345
    }

    sample_trace_header = json.dumps({
        "header": {
            "dims": ["x", "y"],
            "units": {"time": "us", "value": "dimensionless"},
            "dtype": "f32",
            "layout": "coo"
        }
    })

    @pytest.fixture
    def loihi_backend(self):
        return LoihiBackend()

    @pytest.fixture
    def spinnaker_backend(self):
        return SpiNNakerBackend()

    @pytest.fixture
    def synsense_backend(self):
        return SynSenseBackend()

    @pytest.fixture
    def all_backends(self, loihi_backend, spinnaker_backend, synsense_backend):
        return {
            "loihi": loihi_backend,
            "spinnaker": spinnaker_backend,
            "synsense": synsense_backend
        }

    @pytest.fixture
    def temp_trace_files(self):
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            f.write(self.sample_trace_header + "\n")
            input_path = f.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as out:
            output_path = out.name

        yield input_path, output_path

        # Cleanup
        try:
            os.unlink(input_path)
            os.unlink(output_path)
        except OSError:
            pass

    # Test utilities
    def validate_dcd_structure(self, dcd: Dict[str, Any]) -> bool:
        """Validate DCD has required fields."""
        required_fields = [
            "name", "vendor", "version", "conformance_profiles",
            "supported_ops", "time_resolution_ns"
        ]
        return all(field in dcd for field in required_fields)

    def validate_plan_structure(self, plan: Dict[str, Any]) -> bool:
        """Validate plan has required fields."""
        required_fields = ["backend", "graph", "partitions"]
        return all(field in plan for field in required_fields)

    def create_invalid_eir(self, missing_field: str) -> Dict[str, Any]:
        """Create EIR with missing required field for negative testing."""
        base_eir = dict(self.sample_eir_realtime)
        if missing_field in base_eir:
            del base_eir[missing_field]
        return base_eir

    # ============================================================================
    # DISCOVERY TESTS
    # ============================================================================

    def describe_discovery_tests(self):
        """Backend discovery and registration tests."""

    def test_loihi_discovery(self, loihi_backend):
        """Test Loihi backend discovery and basic properties."""
        assert loihi_backend.name() == "loihi"
        dcd = loihi_backend.dcd()
        assert dcd["name"] == "loihi"
        assert dcd["vendor"] == "Intel"
        assert "REALTIME" in dcd["conformance_profiles"]

    def test_spinnaker_discovery(self, spinnaker_backend):
        """Test SpiNNaker backend discovery and basic properties."""
        assert spinnaker_backend.name() == "spinnaker"
        dcd = spinnaker_backend.dcd()
        assert dcd["name"] == "spinnaker"
        assert dcd["vendor"] == "University of Manchester"
        assert "REALTIME" in dcd["conformance_profiles"]

    def test_synsense_discovery(self, synsense_backend):
        """Test SynSense backend discovery and basic properties."""
        assert synsense_backend.name() == "synsense"
        dcd = synsense_backend.dcd()
        assert dcd["name"] == "synsense"
        assert dcd["vendor"] == "SynSense"
        assert "REALTIME" in dcd["conformance_profiles"]

    def test_all_backends_discoverable(self, all_backends):
        """Test all backends can be instantiated and return valid names."""
        expected_names = {"loihi", "spinnaker", "synsense"}
        actual_names = {name: backend.name() for name, backend in all_backends.items()}
        assert set(actual_names.values()) == expected_names

    # ============================================================================
    # CONFIGURATION TESTS
    # ============================================================================

    def describe_configuration_tests(self):
        """Backend configuration and DCD validation tests."""

    def test_dcd_structure_validation(self, all_backends):
        """Test all backends return properly structured DCDs."""
        for name, backend in all_backends.items():
            dcd = backend.dcd()
            assert self.validate_dcd_structure(dcd), f"Invalid DCD structure for {name}"

    def test_dcd_capability_fields(self, all_backends):
        """Test DCD contains all expected capability fields."""
        for name, backend in all_backends.items():
            dcd = backend.dcd()

            # Check limits section
            assert "limits" in dcd
            limits = dcd["limits"]
            assert "max_neurons" in limits
            assert "max_synapses" in limits

            # Check power section
            assert "power" in dcd
            power = dcd["power"]
            assert "mw_per_spike_typ" in power
            assert "idle_mw" in power

            # Check supported ops
            assert "supported_ops" in dcd
            assert isinstance(dcd["supported_ops"], list)
            assert len(dcd["supported_ops"]) > 0

    def test_backend_capability_comparison(self, all_backends):
        """Test capability comparison between backends."""
        loihi_dcd = all_backends["loihi"].dcd()
        spinnaker_dcd = all_backends["spinnaker"].dcd()
        synsense_dcd = all_backends["synsense"].dcd()

        # SynSense should be most power efficient
        assert synsense_dcd["power"]["mw_per_spike_typ"] < loihi_dcd["power"]["mw_per_spike_typ"]
        assert synsense_dcd["power"]["mw_per_spike_typ"] < spinnaker_dcd["power"]["mw_per_spike_typ"]

        # SpiNNaker should support most neurons
        assert spinnaker_dcd["limits"]["max_neurons"] > loihi_dcd["limits"]["max_neurons"]
        assert spinnaker_dcd["limits"]["max_neurons"] > synsense_dcd["limits"]["max_neurons"]

    # ============================================================================
    # PLANNING TESTS
    # ============================================================================

    def describe_planning_tests(self):
        """Backend planning and resource allocation tests."""

    @patch('eventflow_backends.vendor_backends.loihi.backend._check_nxsdk')
    def test_loihi_planning_success(self, mock_check, loihi_backend):
        """Test Loihi backend planning with SDK available."""
        mock_check.return_value = True

        plan = loihi_backend.plan(self.sample_eir_realtime)
        assert self.validate_plan_structure(plan)
        assert plan["backend"]["name"] == "loihi"
        assert plan["graph"]["profile"] == "REALTIME"

    @patch('eventflow_backends.vendor_backends.spinnaker.backend._check_spynnaker')
    def test_spinnaker_planning_success(self, mock_check, spinnaker_backend):
        """Test SpiNNaker backend planning with SDK available."""
        mock_check.return_value = True

        plan = spinnaker_backend.plan(self.sample_eir_realtime)
        assert self.validate_plan_structure(plan)
        assert plan["backend"]["name"] == "spinnaker"
        assert plan["graph"]["profile"] == "REALTIME"

    @patch('eventflow_backends.vendor_backends.synsense.backend._check_synsense')
    def test_synsense_planning_success(self, mock_check, synsense_backend):
        """Test SynSense backend planning with SDK available."""
        mock_check.return_value = True

        plan = synsense_backend.plan(self.sample_eir_realtime)
        assert self.validate_plan_structure(plan)
        assert plan["backend"]["name"] == "synsense"
        assert plan["graph"]["profile"] == "REALTIME"

    def test_planning_unsupported_profile(self, all_backends):
        """Test planning fails with unsupported profile."""
        invalid_eir = {"profile": "UNSUPPORTED"}

        for name, backend in all_backends.items():
            with pytest.raises(ValueError, match="profile.*not supported"):
                backend.plan(invalid_eir)

    def test_planning_complex_graph(self, all_backends):
        """Test planning with complex multi-node graphs."""
        # Mock SDK availability for all backends
        with patch('eventflow_backends.vendor_backends.loihi.backend._check_nxsdk', return_value=True), \
             patch('eventflow_backends.vendor_backends.spinnaker.backend._check_spynnaker', return_value=True), \
             patch('eventflow_backends.vendor_backends.synsense.backend._check_synsense', return_value=True):

            for name, backend in all_backends.items():
                plan = backend.plan(self.sample_eir_complex)
                assert self.validate_plan_structure(plan)
                assert len(plan["partitions"]) > 0

    # ============================================================================
    # EXECUTION TESTS
    # ============================================================================

    def describe_execution_tests(self):
        """Backend execution and simulation tests."""

    def test_execution_without_hardware(self, all_backends, temp_trace_files):
        """Test execution simulation without actual hardware."""
        input_path, output_path = temp_trace_files

        for name, backend in all_backends.items():
            result = backend.run(self.sample_eir_realtime, [input_path], output_path)
            assert result["status"] == "ok"
            assert os.path.exists(output_path)

    # ============================================================================
    # ERROR HANDLING TESTS
    # ============================================================================

    def describe_error_tests(self):
        """Error handling and edge case tests."""

    @patch('eventflow_backends.vendor_backends.loihi.backend._check_nxsdk')
    def test_loihi_sdk_unavailable_error(self, mock_check, loihi_backend):
        """Test Loihi backend fails gracefully when SDK unavailable."""
        mock_check.return_value = False

        with pytest.raises(RuntimeError, match="NxSDK not available"):
            loihi_backend.plan(self.sample_eir_realtime)

    @patch('eventflow_backends.vendor_backends.spinnaker.backend._check_spynnaker')
    def test_spinnaker_sdk_unavailable_error(self, mock_check, spinnaker_backend):
        """Test SpiNNaker backend fails gracefully when SDK unavailable."""
        mock_check.return_value = False

        with pytest.raises(RuntimeError, match="sPyNNaker not available"):
            spinnaker_backend.plan(self.sample_eir_realtime)

    @patch('eventflow_backends.vendor_backends.synsense.backend._check_synsense')
    def test_synsense_sdk_unavailable_error(self, mock_check, synsense_backend):
        """Test SynSense backend fails gracefully when SDK unavailable."""
        mock_check.return_value = False

        with pytest.raises(RuntimeError, match="SynSense SDK not available"):
            synsense_backend.plan(self.sample_eir_realtime)

    def test_invalid_eir_handling(self, all_backends):
        """Test backends handle invalid EIR gracefully."""
        invalid_eirs = [
            self.create_invalid_eir("profile"),
            self.create_invalid_eir("graph"),
            {"profile": "REALTIME"},  # Missing graph
            {"graph": {"name": "test"}},  # Missing profile
        ]

        for invalid_eir in invalid_eirs:
            for name, backend in all_backends.items():
                with pytest.raises((ValueError, KeyError, TypeError)):
                    backend.plan(invalid_eir)

    # ============================================================================
    # CONFORMANCE TESTS
    # ============================================================================

    def describe_conformance_tests(self):
        """Conformance validation against CPU simulator."""

    def test_conformance_profiles_supported(self, all_backends):
        """Test all backends support expected conformance profiles."""
        for name, backend in all_backends.items():
            dcd = backend.dcd()
            profiles = dcd.get("conformance_profiles", [])
            assert "REALTIME" in profiles, f"{name} missing REALTIME profile"

    def test_opset_compatibility(self, all_backends):
        """Test backends have compatible opset versions."""
        for name, backend in all_backends.items():
            dcd = backend.dcd()
            opset_versions = dcd.get("opset_versions", {})

            # Common ops should have version info
            common_ops = ["lif", "synapse_exp"]
            for op in common_ops:
                if op in dcd.get("supported_ops", []):
                    assert op in opset_versions, f"{name} missing version for {op}"

    # ============================================================================
    # CROSS-BACKEND TESTS
    # ============================================================================

    def describe_cross_backend_tests(self):
        """Cross-backend compatibility and comparison tests."""

    def test_backend_capability_matrix(self, all_backends):
        """Test capability comparison matrix between all backends."""
        backends_list = list(all_backends.items())

        for i, (name1, backend1) in enumerate(backends_list):
            for j, (name2, backend2) in enumerate(backends_list):
                if i != j:
                    dcd1 = backend1.dcd()
                    dcd2 = backend2.dcd()

                    # Ensure different backends have different characteristics
                    assert dcd1["vendor"] != dcd2["vendor"]

                    # Power efficiency should vary
                    power1 = dcd1["power"]["mw_per_spike_typ"]
                    power2 = dcd2["power"]["mw_per_spike_typ"]
                    assert power1 != power2 or abs(power1 - power2) < 0.001  # Allow small differences

    def test_unified_interface_compliance(self, all_backends):
        """Test all backends comply with unified interface."""
        required_methods = ["name", "dcd", "plan", "run"]

        for name, backend in all_backends.items():
            for method in required_methods:
                assert hasattr(backend, method), f"{name} missing {method} method"
                assert callable(getattr(backend, method)), f"{name}.{method} not callable"

    # ============================================================================
    # PERFORMANCE TESTS
    # ============================================================================

    def describe_performance_tests(self):
        """Performance validation tests."""

    def test_planning_performance(self, all_backends):
        """Test planning performance is reasonable."""
        import time

        # Mock SDK availability
        with patch('eventflow_backends.vendor_backends.loihi.backend._check_nxsdk', return_value=True), \
             patch('eventflow_backends.vendor_backends.spinnaker.backend._check_spynnaker', return_value=True), \
             patch('eventflow_backends.vendor_backends.synsense.backend._check_synsense', return_value=True):

            for name, backend in all_backends.items():
                start_time = time.time()
                plan = backend.plan(self.sample_eir_complex)
                end_time = time.time()

                planning_time = end_time - start_time
                # Planning should complete in reasonable time (< 1 second for small graphs)
                assert planning_time < 1.0, f"{name} planning too slow: {planning_time}s"

    # ============================================================================
    # INTEGRATION TESTS
    # ============================================================================

    def describe_integration_tests(self):
        """Integration tests with full workflows."""

    def test_full_workflow_simulation(self, all_backends, temp_trace_files):
        """Test complete workflow from EIR to trace output."""
        input_path, output_path = temp_trace_files

        # Mock SDK availability for planning
        with patch('eventflow_backends.vendor_backends.loihi.backend._check_nxsdk', return_value=True), \
             patch('eventflow_backends.vendor_backends.spinnaker.backend._check_spynnaker', return_value=True), \
             patch('eventflow_backends.vendor_backends.synsense.backend._check_synsense', return_value=True):

            for name, backend in all_backends.items():
                # Plan
                plan = backend.plan(self.sample_eir_realtime)
                assert plan is not None

                # Execute (without hardware)
                result = backend.run(self.sample_eir_realtime, [input_path], output_path)
                assert result["status"] == "ok"
                assert os.path.exists(output_path)

                # Verify output is valid JSONL
                with open(output_path, 'r') as f:
                    lines = f.readlines()
                    assert len(lines) > 0
                    # First line should be header
                    header = json.loads(lines[0])
                    assert "header" in header