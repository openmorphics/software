"""
Base classes and interfaces for EventFlow functional modules.

This module provides the foundation for plug-and-play functional components
that can be mixed and matched to create custom neuromorphic applications.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum
import logging


class FunctionalModuleError(Exception):
    """Base exception for functional module errors"""
    pass


class ModuleConfigurationError(FunctionalModuleError):
    """Raised when module configuration is invalid"""
    pass


class ModuleInitializationError(FunctionalModuleError):
    """Raised when module initialization fails"""
    pass


class ModuleExecutionError(FunctionalModuleError):
    """Raised when module execution fails"""
    pass


# Set up logging
logger = logging.getLogger(__name__)


class ModuleType(Enum):
    """Types of functional modules"""
    PROCESSING = "processing"
    NEURON = "neuron"
    SENSOR = "sensor"
    ALGORITHM = "algorithm"
    CONTROL = "control"
    FUSION = "fusion"
    GENERATIVE = "generative"
    TRANSFORM = "transform"


class DataFormat(Enum):
    """Supported data formats for functional modules"""
    EVENT_TENSOR = "event_tensor"
    NUMPY_ARRAY = "numpy_array"
    PANDAS_DF = "pandas_dataframe"
    CUSTOM = "custom"


@dataclass
class ModuleCapabilities:
    """Capabilities declaration for functional modules"""
    module_type: ModuleType
    supported_backends: List[str]
    input_formats: List[DataFormat]
    output_formats: List[DataFormat]
    max_latency_ms: float
    memory_mb: float
    energy_efficiency: float  # operations per joule
    deterministic: bool
    real_time_capable: bool


@dataclass
class ModuleRequirements:
    """Requirements for functional modules"""
    min_python_version: str
    dependencies: List[str]
    hardware_requirements: Dict[str, Any]
    input_constraints: Dict[str, Any]
    output_constraints: Dict[str, Any]


class FunctionalModule(ABC):
    """
    Base class for all functional modules in EventFlow.

    Functional modules are plug-and-play components that implement specific
    neuromorphic computing functions and can be composed together to create
    custom applications.
    """

    # Compatibility aliases used by older module implementations.
    DataFormat = DataFormat
    ModuleType = ModuleType

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize functional module.

        Args:
            config: Module configuration parameters
        """
        self.config = config.copy()
        self.name = config.get('name', self.__class__.__name__.lower())
        self.version = config.get('version', '1.0.0')

        # Declare capabilities and requirements
        self.capabilities = self._declare_capabilities()
        self.requirements = self._declare_requirements()

        # Runtime state
        self.initialized = False
        self.last_execution_time = 0.0
        self.execution_count = 0

        # Validate configuration
        self._validate_config(config)

        # Set up logger for this module instance
        self.logger = logging.getLogger(f"{__name__}.{self.name}")

    @abstractmethod
    def _declare_capabilities(self) -> ModuleCapabilities:
        """Declare module capabilities (must be implemented by subclasses)"""
        pass

    @abstractmethod
    def _declare_requirements(self) -> ModuleRequirements:
        """Declare module requirements (must be implemented by subclasses)"""
        pass

    @abstractmethod
    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Process input data through functional transformation.

        Args:
            inputs: Input data in supported format

        Returns:
            Processed output data
        """
        pass

    def validate_inputs(self, inputs: Union[Any, Dict[str, Any]]) -> bool:
        """
        Validate input data against module requirements.

        Args:
            inputs: Input data to validate

        Returns:
            True if inputs are valid, False otherwise
        """
        try:
            self._validate_input_format(inputs)
            self._validate_input_constraints(inputs)
            return True
        except (ValueError, TypeError) as e:
            self.logger.error(f"Input validation failed for module {self.name}: {e}")
            return False

    def validate_outputs(self, outputs: Union[Any, Dict[str, Any]]) -> bool:
        """
        Validate output data against module requirements.

        Args:
            outputs: Output data to validate

        Returns:
            True if outputs are valid, False otherwise
        """
        try:
            self._validate_output_format(outputs)
            self._validate_output_constraints(outputs)
            return True
        except (ValueError, TypeError) as e:
            self.logger.error(f"Output validation failed for module {self.name}: {e}")
            return False

    def _validate_input_format(self, inputs: Union[Any, Dict[str, Any]]) -> None:
        """Validate input data format (can be overridden)"""
        # Basic format validation based on declared capabilities.
        if isinstance(inputs, dict):
            if not inputs:
                raise ValueError("Input payload cannot be empty")
            if DataFormat.EVENT_TENSOR in self.capabilities.input_formats and "events" not in inputs:
                raise ValueError("Expected 'events' key for EVENT_TENSOR inputs")
        elif hasattr(inputs, '__array__') and DataFormat.NUMPY_ARRAY not in self.capabilities.input_formats:
            raise ValueError(f"NumPy array inputs not supported by module {self.name}")

    def _validate_output_format(self, outputs: Union[Any, Dict[str, Any]]) -> None:
        """Validate output data format (can be overridden)"""
        # Basic format validation based on capabilities
        if isinstance(outputs, dict) and DataFormat.CUSTOM not in self.capabilities.output_formats:
            pass  # Custom validation logic can be added here
        elif hasattr(outputs, '__array__') and DataFormat.NUMPY_ARRAY not in self.capabilities.output_formats:
            raise ValueError(f"NumPy array outputs not supported by module {self.name}")

    def _validate_input_constraints(self, inputs: Union[Any, Dict[str, Any]]) -> None:
        """Validate input constraints (can be overridden)"""
        # Check constraints only when data provides the referenced keys.
        constraints = self.requirements.input_constraints
        if constraints and isinstance(inputs, dict):
            for key, expected_value in constraints.items():
                if key not in inputs:
                    continue
                if isinstance(expected_value, bool):
                    if bool(inputs[key]) != expected_value:
                        raise ValueError(f"Input constraint '{key}' expected {expected_value}")
                elif inputs[key] != expected_value:
                    raise ValueError(f"Input constraint '{key}' expected {expected_value}")

    def _validate_output_constraints(self, outputs: Union[Any, Dict[str, Any]]) -> None:
        """Validate output constraints (can be overridden)"""
        # Check basic constraints from requirements
        constraints = self.requirements.output_constraints
        if constraints:
            for key, expected_value in constraints.items():
                if isinstance(expected_value, bool) and key not in outputs:
                    raise ValueError(f"Required output constraint '{key}' not satisfied")

    def configure(self, params: Dict[str, Any]) -> bool:
        """
        Runtime parameter reconfiguration.

        Args:
            params: New parameter values

        Returns:
            Success status
        """
        try:
            # Validate new parameters
            self._validate_config({**self.config, **params})

            # Update configuration
            self.config.update(params)

            # Reinitialize if necessary
            if self.initialized:
                self._reinitialize()

            self.logger.info(f"Configuration updated successfully for module {self.name}")
            return True
        except Exception as e:
            self.logger.error(f"Configuration update failed for module {self.name}: {e}")
            raise ModuleConfigurationError(f"Failed to update configuration: {e}") from e

    def get_metadata(self) -> Dict[str, Any]:
        """Get complete module metadata"""
        return {
            'name': self.name,
            'version': self.version,
            'type': self.capabilities.module_type.value,
            'capabilities': {
                'backends': self.capabilities.supported_backends,
                'input_formats': [f.value for f in self.capabilities.input_formats],
                'output_formats': [f.value for f in self.capabilities.output_formats],
                'max_latency_ms': self.capabilities.max_latency_ms,
                'memory_mb': self.capabilities.memory_mb,
                'energy_efficiency': self.capabilities.energy_efficiency,
                'deterministic': self.capabilities.deterministic,
                'real_time': self.capabilities.real_time_capable
            },
            'requirements': {
                'python_version': self.requirements.min_python_version,
                'dependencies': self.requirements.dependencies,
                'hardware': self.requirements.hardware_requirements
            },
            'runtime': {
                'initialized': self.initialized,
                'execution_count': self.execution_count,
                'last_execution_time': self.last_execution_time,
                'avg_execution_time': self._get_avg_execution_time()
            }
        }

    def initialize(self) -> bool:
        """Initialize module for processing"""
        try:
            if not self.initialized:
                self.logger.info(f"Initializing module {self.name}")
                self._initialize()
                self.initialized = True
                self.logger.info(f"Module {self.name} initialized successfully")
            return True
        except Exception as e:
            self.logger.error(f"Initialization failed for module {self.name}: {e}")
            raise ModuleInitializationError(f"Failed to initialize module {self.name}: {e}") from e

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate module configuration (can be overridden)"""
        pass

    def _initialize(self) -> None:
        """Module-specific initialization (can be overridden)"""
        pass

    def _reinitialize(self) -> None:
        """Handle reconfiguration (can be overridden)"""
        pass

    def _get_avg_execution_time(self) -> float:
        """Calculate average execution time"""
        if self.execution_count == 0:
            return 0.0
        return self.last_execution_time / self.execution_count


class ProcessingModule(FunctionalModule):
    """Base class for processing functional modules (filtering, features, etc.)"""

    def _declare_capabilities(self) -> ModuleCapabilities:
        return ModuleCapabilities(
            module_type=ModuleType.PROCESSING,
            supported_backends=['cpu-sim', 'gpu-sim', 'loihi-sim', 'spinnaker-sim'],
            input_formats=[DataFormat.EVENT_TENSOR],
            output_formats=[DataFormat.EVENT_TENSOR],
            max_latency_ms=10.0,
            memory_mb=50.0,
            energy_efficiency=1000.0,
            deterministic=True,
            real_time_capable=True
        )

    def _declare_requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            min_python_version="3.9",
            dependencies=["numpy", "scipy"],
            hardware_requirements={},
            input_constraints={"dims": [3], "temporal": True},
            output_constraints={"dims": [3], "temporal": True}
        )

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """Default pass-through implementation for compatibility tests."""
        return inputs


class SensorModule(FunctionalModule):
    """Base class for sensor functional modules"""

    def _declare_capabilities(self) -> ModuleCapabilities:
        return ModuleCapabilities(
            module_type=ModuleType.SENSOR,
            supported_backends=['cpu-sim'],
            input_formats=[DataFormat.CUSTOM],
            output_formats=[DataFormat.EVENT_TENSOR],
            max_latency_ms=5.0,
            memory_mb=25.0,
            energy_efficiency=2000.0,
            deterministic=False,  # Sensors may have timing variations
            real_time_capable=True
        )

    def _declare_requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            min_python_version="3.9",
            dependencies=[],
            hardware_requirements={"sensors": "required"},
            input_constraints={},
            output_constraints={"dims": [3], "temporal": True}
        )


class AlgorithmModule(FunctionalModule):
    """Base class for algorithm functional modules (detection, classification, etc.)"""

    def _declare_capabilities(self) -> ModuleCapabilities:
        return ModuleCapabilities(
            module_type=ModuleType.ALGORITHM,
            supported_backends=['cpu-sim', 'gpu-sim', 'loihi-sim'],
            input_formats=[DataFormat.EVENT_TENSOR],
            output_formats=[DataFormat.EVENT_TENSOR],
            max_latency_ms=50.0,
            memory_mb=100.0,
            energy_efficiency=500.0,
            deterministic=True,
            real_time_capable=True
        )

    def _declare_requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            min_python_version="3.9",
            dependencies=["numpy", "scipy"],
            hardware_requirements={},
            input_constraints={"dims": [3], "temporal": True},
            output_constraints={"dims": [2], "classification": True}
        )


class ControlModule(FunctionalModule):
    """Base class for control functional modules (feedback, regulation, etc.)"""

    def _declare_capabilities(self) -> ModuleCapabilities:
        return ModuleCapabilities(
            module_type=ModuleType.CONTROL,
            supported_backends=['cpu-sim', 'gpu-sim'],
            input_formats=[DataFormat.EVENT_TENSOR, DataFormat.NUMPY_ARRAY],
            output_formats=[DataFormat.EVENT_TENSOR],
            max_latency_ms=25.0,
            memory_mb=75.0,
            energy_efficiency=800.0,
            deterministic=True,
            real_time_capable=True
        )

    def _declare_requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            min_python_version="3.9",
            dependencies=["numpy"],
            hardware_requirements={},
            input_constraints={"control_signals": True},
            output_constraints={"actuator_commands": True}
        )


class FusionModule(FunctionalModule):
    """Base class for fusion functional modules (sensor fusion, data integration, etc.)"""

    def _declare_capabilities(self) -> ModuleCapabilities:
        return ModuleCapabilities(
            module_type=ModuleType.FUSION,
            supported_backends=['cpu-sim', 'gpu-sim'],
            input_formats=[DataFormat.EVENT_TENSOR, DataFormat.NUMPY_ARRAY],
            output_formats=[DataFormat.EVENT_TENSOR],
            max_latency_ms=75.0,
            memory_mb=150.0,
            energy_efficiency=400.0,
            deterministic=True,
            real_time_capable=True
        )

    def _declare_requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            min_python_version="3.9",
            dependencies=["numpy", "scipy"],
            hardware_requirements={},
            input_constraints={"multiple_sources": True},
            output_constraints={"fused_data": True}
        )


class GenerativeModule(FunctionalModule):
    """Base class for generative functional modules (synthesis, simulation, etc.)"""

    def _declare_capabilities(self) -> ModuleCapabilities:
        return ModuleCapabilities(
            module_type=ModuleType.GENERATIVE,
            supported_backends=['cpu-sim', 'gpu-sim'],
            input_formats=[DataFormat.EVENT_TENSOR, DataFormat.NUMPY_ARRAY],
            output_formats=[DataFormat.EVENT_TENSOR],
            max_latency_ms=100.0,
            memory_mb=200.0,
            energy_efficiency=300.0,
            deterministic=False,  # Generative modules may have stochastic elements
            real_time_capable=False  # Typically not real-time
        )

    def _declare_requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            min_python_version="3.9",
            dependencies=["numpy", "scipy"],
            hardware_requirements={},
            input_constraints={"seed_data": True},
            output_constraints={"synthetic_data": True}
        )


class TransformModule(FunctionalModule):
    """Base class for transform functional modules (data conversion, normalization, etc.)"""

    def _declare_capabilities(self) -> ModuleCapabilities:
        return ModuleCapabilities(
            module_type=ModuleType.TRANSFORM,
            supported_backends=['cpu-sim', 'gpu-sim'],
            input_formats=[DataFormat.EVENT_TENSOR, DataFormat.NUMPY_ARRAY, DataFormat.PANDAS_DF],
            output_formats=[DataFormat.EVENT_TENSOR, DataFormat.NUMPY_ARRAY],
            max_latency_ms=15.0,
            memory_mb=50.0,
            energy_efficiency=1200.0,
            deterministic=True,
            real_time_capable=True
        )

    def _declare_requirements(self) -> ModuleRequirements:
        return ModuleRequirements(
            min_python_version="3.9",
            dependencies=["numpy"],
            hardware_requirements={},
            input_constraints={},
            output_constraints={"transformed": True}
        )


class FunctionalRegistry:
    """
    Registry for functional modules with discovery and compatibility checking.
    """

    def __init__(self):
        self.modules: Dict[str, FunctionalModule] = {}
        self.categories: Dict[str, List[str]] = {}

    def register(self, module: FunctionalModule, category: str = None) -> None:
        """Register a functional module"""
        self.modules[module.name] = module

        if category:
            if category not in self.categories:
                self.categories[category] = []
            self.categories[category].append(module.name)

    def get_module(self, name: str) -> Optional[FunctionalModule]:
        """Get module by name"""
        return self.modules.get(name)

    def find_by_function(self, function_type: str) -> List[FunctionalModule]:
        """Find modules by function type"""
        return [
            module for module in self.modules.values()
            if module.capabilities.module_type.value == function_type
        ]

    def find_by_category(self, category: str) -> List[FunctionalModule]:
        """Find modules by category"""
        module_names = self.categories.get(category, [])
        return [self.modules[name] for name in module_names if name in self.modules]

    def check_compatibility(self, modules: List[FunctionalModule]) -> Dict[str, Any]:
        """Check compatibility between modules for composition"""
        if len(modules) < 2:
            return {'compatible': True, 'issues': []}

        issues = []

        for i in range(len(modules) - 1):
            current = modules[i]
            next_module = modules[i + 1]

            # Check output/input format compatibility
            current_output = current.capabilities.output_formats
            next_input = next_module.capabilities.input_formats

            compatible_formats = set(current_output) & set(next_input)
            if not compatible_formats:
                issues.append({
                    'type': 'format_mismatch',
                    'modules': [current.name, next_module.name],
                    'message': f'Output formats {current_output} incompatible with input formats {next_input}'
                })

            # Check latency compatibility for real-time applications
            if current.capabilities.real_time_capable and next_module.capabilities.real_time_capable:
                total_latency = current.capabilities.max_latency_ms + next_module.capabilities.max_latency_ms
                if total_latency > 100:  # Arbitrary real-time threshold
                    issues.append({
                        'type': 'latency_warning',
                        'modules': [current.name, next_module.name],
                        'message': f'Combined latency {total_latency}ms may exceed real-time requirements'
                    })

        return {
            'compatible': len(issues) == 0,
            'issues': issues
        }

    def compose(self, module_names: List[str]) -> Optional[List[FunctionalModule]]:
        """Compose modules into a pipeline"""
        modules = []
        for name in module_names:
            module = self.get_module(name)
            if not module:
                logger.error(f"Module {name} not found in registry")
                return None
            modules.append(module)

        compatibility = self.check_compatibility(modules)
        if not compatibility['compatible']:
            logger.error(f"Module composition incompatible: {compatibility['issues']}")
            return None

        return modules

    def get_available_modules(self) -> Dict[str, Dict[str, Any]]:
        """Get all available modules with metadata"""
        return {
            name: module.get_metadata()
            for name, module in self.modules.items()
        }

    def validate_module_capabilities(self, module: FunctionalModule, backend: str = None) -> Dict[str, Any]:
        """
        Validate that a module meets its declared capabilities and requirements.

        Args:
            module: The module to validate
            backend: Optional specific backend to check against

        Returns:
            Validation results with any issues found
        """
        issues = []

        # Check backend compatibility
        if backend and backend not in module.capabilities.supported_backends:
            issues.append({
                'type': 'backend_incompatible',
                'message': f'Module {module.name} does not support backend {backend}',
                'supported_backends': module.capabilities.supported_backends
            })

        # Check real-time capability if required
        if hasattr(module.config, 'require_real_time') and module.config.get('require_real_time'):
            if not module.capabilities.real_time_capable:
                issues.append({
                    'type': 'real_time_incompatible',
                    'message': f'Module {module.name} is not real-time capable'
                })

        # Check latency requirements
        max_allowed_latency = module.config.get('max_allowed_latency_ms')
        if max_allowed_latency and module.capabilities.max_latency_ms > max_allowed_latency:
            issues.append({
                'type': 'latency_exceeded',
                'message': f'Module latency {module.capabilities.max_latency_ms}ms exceeds limit {max_allowed_latency}ms'
            })

        return {
            'module_name': module.name,
            'valid': len(issues) == 0,
            'issues': issues,
            'capabilities': {
                'supported_backends': module.capabilities.supported_backends,
                'max_latency_ms': module.capabilities.max_latency_ms,
                'real_time_capable': module.capabilities.real_time_capable,
                'memory_mb': module.capabilities.memory_mb
            }
        }

    def find_modules_by_capability(self,
                                 module_type: ModuleType = None,
                                 backend: str = None,
                                 max_latency_ms: float = None,
                                 real_time_required: bool = False) -> List[FunctionalModule]:
        """
        Find modules that match specific capability requirements.

        Args:
            module_type: Required module type
            backend: Required backend support
            max_latency_ms: Maximum allowed latency
            real_time_required: Whether real-time capability is required

        Returns:
            List of matching modules
        """
        matching_modules = []

        for module in self.modules.values():
            # Check module type
            if module_type and module.capabilities.module_type != module_type:
                continue

            # Check backend support
            if backend and backend not in module.capabilities.supported_backends:
                continue

            # Check latency
            if max_latency_ms and module.capabilities.max_latency_ms > max_latency_ms:
                continue

            # Check real-time capability
            if real_time_required and not module.capabilities.real_time_capable:
                continue

            matching_modules.append(module)

        return matching_modules


# Global registry instance
functional_registry = FunctionalRegistry()


def register_functional_module(
    module_or_class: Union[FunctionalModule, type],
    config: Optional[Dict[str, Any]] = None,
    category: str = None
) -> FunctionalModule:
    """
    Convenience function to register a functional module.

    Args:
        module_or_class: Instantiated module or module class to instantiate
        config: Module configuration when module_or_class is a class
        category: Optional category for organization

    Returns:
        Registered module instance
    """
    if isinstance(module_or_class, FunctionalModule):
        module = module_or_class
        if isinstance(config, str) and category is None:
            category = config
    else:
        if not isinstance(config, dict):
            raise TypeError("config dict is required when registering by class")
        module = module_or_class(config)

    functional_registry.register(module, category)
    return module
