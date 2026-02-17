"""
Tests for functional modules architecture.

This module provides comprehensive tests for the functional modules
architecture, including base classes, concrete implementations,
registry operations, and error handling.
"""

import unittest
import numpy as np
from eventflow_modules.functions import (
    FunctionalModule, FunctionalRegistry, ProcessingModule,
    EventFilterModule, AnomalyDetector, TemporalFilter,
    functional_registry, register_functional_module,
    FunctionalModuleError, ModuleConfigurationError
)


class TestFunctionalModules(unittest.TestCase):
    """Test cases for functional modules architecture."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_events = [
            {'timestamp': 1000, 'x': 10, 'y': 20, 'amplitude': 0.3},
            {'timestamp': 1001, 'x': 15, 'y': 25, 'amplitude': 0.8},
            {'timestamp': 1002, 'x': 12, 'y': 18, 'amplitude': 0.2},
            {'timestamp': 1003, 'x': 20, 'y': 30, 'amplitude': 0.9},
            {'timestamp': 1004, 'x': 8, 'y': 15, 'amplitude': 0.1},
        ]

    def test_base_module_creation(self):
        """Test basic module creation and configuration."""
        config = {'name': 'test_module', 'version': '1.0.0'}
        module = ProcessingModule(config)

        self.assertEqual(module.name, 'test_module')
        self.assertEqual(module.version, '1.0.0')
        self.assertFalse(module.initialized)

        # Test metadata
        metadata = module.get_metadata()
        self.assertIn('capabilities', metadata)
        self.assertIn('requirements', metadata)
        self.assertIn('runtime', metadata)

    def test_module_initialization(self):
        """Test module initialization."""
        module = EventFilterModule({'name': 'filter_test'})
        self.assertFalse(module.initialized)

        success = module.initialize()
        self.assertTrue(success)
        self.assertTrue(module.initialized)

    def test_event_filter_module(self):
        """Test EventFilterModule functionality."""
        config = {'name': 'event_filter', 'threshold': 0.5}
        module = EventFilterModule(config)

        input_data = {'events': self.sample_events}
        result = module.process(input_data)

        # Should filter out events below threshold
        self.assertIn('events', result)
        self.assertIn('filtered_count', result)
        self.assertGreater(result['filtered_count'], 0)

        # Check that filtered events have required amplitude
        for event in result['events']:
            self.assertGreaterEqual(event.get('amplitude', 0), 0.5)

    def test_anomaly_detector(self):
        """Test AnomalyDetector functionality."""
        config = {'name': 'anomaly_det', 'threshold': 1.5}
        module = AnomalyDetector(config)

        # Create events with one clear anomaly
        normal_events = [
            {'timestamp': i, 'amplitude': 0.5 + 0.1 * np.sin(i * 0.1)}
            for i in range(50)
        ]
        anomaly_events = normal_events + [{'timestamp': 50, 'amplitude': 3.0}]  # Clear anomaly

        input_data = {'events': anomaly_events}
        result = module.process(input_data)

        self.assertIn('anomalies', result)
        self.assertIn('total_events', result)
        self.assertIn('anomaly_rate', result)

        # Should detect the anomaly
        self.assertGreater(len(result['anomalies']), 0)

    def test_temporal_filter(self):
        """Test TemporalFilter functionality."""
        config = {'name': 'temp_filter', 'filter_type': 'mean', 'window_size': 3}
        module = TemporalFilter(config)

        # Create events with noise
        noisy_events = [
            {'timestamp': i, 'amplitude': 1.0 + 0.5 * np.random.randn()}
            for i in range(10)
        ]

        input_data = {'events': noisy_events}
        result = module.process(input_data)

        self.assertIn('events', result)
        self.assertEqual(len(result['events']), len(noisy_events))

        # Check that filtered amplitudes are added
        for event in result['events']:
            self.assertIn('filtered_amplitude', event)
            self.assertIn('original_amplitude', event)

    def test_module_validation(self):
        """Test input/output validation."""
        module = EventFilterModule({'name': 'validator_test'})

        # Test valid input
        valid_input = {'events': self.sample_events}
        self.assertTrue(module.validate_inputs(valid_input))

        # Test invalid input (empty dict)
        invalid_input = {}
        self.assertFalse(module.validate_inputs(invalid_input))

    def test_registry_operations(self):
        """Test registry functionality."""
        # Create test modules
        module1 = EventFilterModule({'name': 'reg_test_1'})
        module2 = AnomalyDetector({'name': 'reg_test_2'})

        # Register modules
        register_functional_module(module1, 'test_category')
        register_functional_module(module2, 'test_category')

        # Test retrieval
        retrieved1 = functional_registry.get_module('reg_test_1')
        self.assertIsNotNone(retrieved1)
        self.assertEqual(retrieved1.name, 'reg_test_1')

        # Test category finding
        category_modules = functional_registry.find_by_category('test_category')
        self.assertEqual(len(category_modules), 2)

    def test_module_capability_validation(self):
        """Test capability validation."""
        module = EventFilterModule({'name': 'cap_test'})

        # Test valid backend
        validation = functional_registry.validate_module_capabilities(
            module, 'cpu-sim'
        )
        self.assertTrue(validation['valid'])

        # Test invalid backend (if module doesn't support it)
        # This depends on the module's declared capabilities

    def test_configuration_error_handling(self):
        """Test configuration error handling."""
        # Test with invalid configuration
        with self.assertRaises(ModuleConfigurationError):
            # This should fail due to invalid config validation
            module = EventFilterModule({'invalid_param': 'should_fail'})

    def test_module_composition(self):
        """Test module composition and compatibility."""
        module1 = EventFilterModule({'name': 'comp_test_1'})
        module2 = AnomalyDetector({'name': 'comp_test_2'})

        # Test composition
        pipeline = functional_registry.compose(['comp_test_1', 'comp_test_2'])
        # Composition may fail due to format incompatibilities, which is expected
        # The important thing is that the method runs without crashing

    def tearDown(self):
        """Clean up test fixtures."""
        # Remove test modules from registry
        test_modules = ['reg_test_1', 'reg_test_2', 'comp_test_1', 'comp_test_2']
        for module_name in test_modules:
            if module_name in functional_registry.modules:
                del functional_registry.modules[module_name]


if __name__ == '__main__':
    unittest.main()