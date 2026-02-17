"""
EventFlow Functional Modules

Plug-and-play functional components for neuromorphic computing.
Mix and match functions to create custom applications across domains.
"""

from .base import (
    FunctionalModule,
    FunctionalRegistry,
    ProcessingModule,
    SensorModule,
    AlgorithmModule,
    ControlModule,
    FusionModule,
    GenerativeModule,
    TransformModule,
    ModuleType,
    DataFormat,
    functional_registry,
    register_functional_module,
    FunctionalModuleError,
    ModuleConfigurationError,
    ModuleInitializationError,
    ModuleExecutionError
)

# Import concrete module implementations
from .example_module import EventFilterModule
from .detection_modules import AnomalyDetector, PatternClassifier, MotionDetector
from .processing_modules import TemporalFilter, SpatialFilter, DataNormalizer, FeatureExtractor
from .vision_modules import OpticalFlowEstimator, CornerDetector, ObjectTracker
from .audio_modules import VoiceActivityDetector, KeywordSpotter, AudioBeamformer
from .robotics_modules import ObstacleAvoidanceController, PathPlanner, MotorController
from .generic_modules import (
    EventBuffer, EventRouter, EventMultiplexer, PerformanceMonitor, ConditionalProcessor,
    StateManager, DataValidator, EventLogger, LoadBalancer, CircuitBreaker,
    RetryHandler, RateLimiter, CacheManager
)


# Legacy registry names retained for compatibility with older imports.
class ProcessingRegistry(FunctionalRegistry):
    """Compatibility alias for older processing registry imports."""


class NeuronRegistry(FunctionalRegistry):
    """Compatibility alias for older neuron registry imports."""


class SensorRegistry(FunctionalRegistry):
    """Compatibility alias for older sensor registry imports."""


class AlgorithmRegistry(FunctionalRegistry):
    """Compatibility alias for older algorithm registry imports."""

__all__ = [
    # Base classes and infrastructure
    'FunctionalModule',
    'FunctionalRegistry',
    'functional_registry',
    'register_functional_module',

    # Module type base classes
    'ProcessingModule',
    'SensorModule',
    'AlgorithmModule',
    'ControlModule',
    'FusionModule',
    'GenerativeModule',
    'TransformModule',

    # Enums and types
    'ModuleType',
    'DataFormat',

    # Exception classes
    'FunctionalModuleError',
    'ModuleConfigurationError',
    'ModuleInitializationError',
    'ModuleExecutionError',

    # Concrete module implementations
    'EventFilterModule',
    'AnomalyDetector',
    'PatternClassifier',
    'MotionDetector',
    'TemporalFilter',
    'SpatialFilter',
    'DataNormalizer',
    'FeatureExtractor',
    'OpticalFlowEstimator',
    'CornerDetector',
    'ObjectTracker',
    'VoiceActivityDetector',
    'KeywordSpotter',
    'AudioBeamformer',
    'ObstacleAvoidanceController',
    'PathPlanner',
    'MotorController',
    'EventBuffer',
    'EventRouter',
    'EventMultiplexer',
    'PerformanceMonitor',
    'ConditionalProcessor',
    'StateManager',
    'DataValidator',
    'EventLogger',
    'LoadBalancer',
    'CircuitBreaker',
    'RetryHandler',
    'RateLimiter',
    'CacheManager',

    # Legacy registry names (for compatibility)
    'ProcessingRegistry',
    'NeuronRegistry',
    'SensorRegistry',
    'AlgorithmRegistry'
]
