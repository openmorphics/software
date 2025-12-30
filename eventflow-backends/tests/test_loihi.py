"""
Comprehensive Loihi Backend Tests

Tests Loihi backend functionality covering discovery, configuration,
planning, execution, error handling, and conformance validation.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch
from eventflow_backends.vendor_backends.loihi.backend import LoihiBackend, _check_nxsdk


class TestLoihiBackend:
    """Loihi backend test suite."""

    @pytest.fixture
    def backend(self):
        """Loihi backend instance."""
        return LoihiBackend()

    @pytest.fixture
    def sample_eir(self):
        """Sample EIR for testing."""
        return {
            "profile": "REALTIME",
            "graph": {"name": "test_graph"},
            "nodes": [
                {"id": "n1", "kind": "spiking_neuron", "op": "lif"},
                {"id": "n2", "kind": "synapse", "op": "synapse_exp"},
            ],
            "edges": [{"from": "n1", "to": "n2"}],
            "seed": 42
        }

    @pytest.fixture
    def temp_trace_files(self):
        """Temporary trace files for testing."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".jsonl") as f:
            f.write('{"header":{"dims":["x","y"],"units":{"time":"us","value":"dimensionless"},"dtype":"f32","layout":"coo"}}\n')
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

    # ============================================================================
    # DISCOVERY TESTS
    # ============================================================================

    def test_backend_discovery(self, backend):
        """Test Loihi backend can be instantiated and discovered."""
        assert backend.name() == "loihi"

    def test_dcd_loading(self, backend):
        """Test DCD is properly loaded and structured."""
        dcd = backend.dcd()

        # Required fields
        assert dcd["name"] == "loihi"
        assert dcd["vendor"] == "Intel"
        assert "REALTIME" in dcd["conformance_profiles"]
        assert "supported_ops" in dcd
        assert "time_resolution_ns" in dcd

        # Loihi-specific capabilities
        assert dcd["time_resolution_ns"] == 1000  # 1μs resolution
        assert dcd["limits"]["max_neurons"] == 131072
        assert "NxSDK" in dcd.get("notes", "")

    # ============================================================================
    # CONFIGURATION TESTS
    # ============================================================================

    def test_dcd_capability_validation(self, backend):
        """Test DCD contains valid capability information."""
        dcd = backend.dcd()

        # Validate limits
        limits = dcd["limits"]
        assert limits["max_neurons"] > 0
        assert limits["max_synapses"] > 0
        assert limits["max_fanout"] > 0

        # Validate power specifications
        power = dcd["power"]
        assert power["mw_per_spike_typ"] > 0
        assert power["idle_mw"] > 0

        # Validate supported ops
        supported_ops = dcd["supported_ops"]
        assert "lif" in supported_ops
        assert "synapse_exp" in supported_ops

    def test_opset_versions(self, backend):
        """Test opset version information is present."""
        dcd = backend.dcd()
        opset_versions = dcd.get("opset_versions", {})

        assert "lif" in opset_versions
        assert "synapse_exp" in opset_versions

        # Versions should be semantic version strings
        for op, version in opset_versions.items():
            assert isinstance(version, str)
            assert len(version.split(".")) >= 2

    # ============================================================================
    # PLANNING TESTS
    # ============================================================================

    @patch('eventflow_backends.vendor_backends.loihi.backend._check_nxsdk')
    def test_planning_with_sdk_available(self, mock_check, backend, sample_eir):
        """Test planning succeeds when NxSDK is available."""
        mock_check.return_value = True

        plan = backend.plan(sample_eir)

        # Validate plan structure
        assert "backend" in plan
        assert "graph" in plan
        assert "partitions" in plan

        assert plan["backend"]["name"] == "loihi"
        assert plan["graph"]["profile"] == "REALTIME"
        assert plan["graph"]["seed"] == 42

    def test_planning_sdk_unavailable(self, backend, sample_eir):
        """Test planning fails gracefully when NxSDK unavailable."""
        with patch('eventflow_backends.vendor_backends.loihi.backend._check_nxsdk', return_value=False):
            with pytest.raises(RuntimeError, match="NxSDK not available"):
                backend.plan(sample_eir)

    def test_planning_unsupported_profile(self, backend):
        """Test planning fails with unsupported profile."""
        invalid_eir = {"profile": "UNSUPPORTED"}

        with patch('eventflow_backends.vendor_backends.loihi.backend._check_nxsdk', return_value=True):
            with pytest.raises(ValueError, match="profile.*not supported"):
                backend.plan(invalid_eir)

    def test_planning_complex_graph(self, backend):
        """Test planning with complex multi-node graph."""
        complex_eir = {
            "profile": "REALTIME",
            "graph": {"name": "complex"},
            "nodes": [
                {"id": "input", "kind": "input", "op": "input_spikes"},
                {"id": "lif1", "kind": "spiking_neuron", "op": "lif"},
                {"id": "lif2", "kind": "spiking_neuron", "op": "lif"},
                {"id": "syn1", "kind": "synapse", "op": "synapse_exp"},
                {"id": "syn2", "kind": "synapse", "op": "synapse_exp"},
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

        with patch('eventflow_backends.vendor_backends.loihi.backend._check_nxsdk', return_value=True):
            plan = backend.plan(complex_eir)
            assert len(plan["partitions"]) > 0

    # ============================================================================
    # EXECUTION TESTS
    # ============================================================================

    def test_execution_simulation(self, backend, sample_eir, temp_trace_files):
        """Test execution simulation without hardware."""
        input_path, output_path = temp_trace_files

        result = backend.run(sample_eir, [input_path], output_path)

        assert result["status"] == "ok"
        assert os.path.exists(output_path)

        # Verify output trace
        with open(output_path, 'r') as f:
            lines = f.readlines()
            assert len(lines) > 0
            header = json.loads(lines[0])
            assert "header" in header

    # ============================================================================
    # ERROR HANDLING TESTS
    # ============================================================================

    def test_invalid_eir_handling(self, backend):
        """Test backend handles invalid EIR gracefully."""
        invalid_eirs = [
            {},  # Empty
            {"profile": "REALTIME"},  # Missing graph
            {"graph": {"name": "test"}},  # Missing profile
            {"profile": "REALTIME", "graph": {"name": "test"}, "nodes": "invalid"},  # Invalid nodes
        ]

        for invalid_eir in invalid_eirs:
            with pytest.raises((ValueError, KeyError, TypeError)):
                backend.plan(invalid_eir)

    def test_missing_input_files(self, backend, sample_eir):
        """Test execution fails gracefully with missing input files."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl") as out:
            output_path = out.name

        try:
            with pytest.raises((FileNotFoundError, OSError)):
                backend.run(sample_eir, ["/nonexistent/file.jsonl"], output_path)
        finally:
            try:
                os.unlink(output_path)
            except OSError:
                pass

    # ============================================================================
    # CONFORMANCE TESTS
    # ============================================================================

    def test_conformance_profile_support(self, backend):
        """Test backend supports required conformance profiles."""
        dcd = backend.dcd()
        profiles = dcd.get("conformance_profiles", [])

        assert "REALTIME" in profiles
        # Loihi should support deterministic execution
        assert dcd.get("deterministic_modes") == ["exact_event"]

    def test_time_resolution_specification(self, backend):
        """Test time resolution is properly specified."""
        dcd = backend.dcd()

        assert dcd["time_resolution_ns"] > 0
        assert dcd["max_jitter_ns"] >= 0  # Loihi should be deterministic

    # ============================================================================
    # PERFORMANCE TESTS
    # ============================================================================

    @patch('eventflow_backends.vendor_backends.loihi.backend._check_nxsdk')
    def test_planning_performance(self, mock_check, backend, sample_eir):
        """Test planning completes in reasonable time."""
        import time

        mock_check.return_value = True

        start_time = time.time()
        plan = backend.plan(sample_eir)
        end_time = time.time()

        planning_time = end_time - start_time
        assert planning_time < 1.0  # Should complete in less than 1 second