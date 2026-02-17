# EventFlow Functional Modules

A plug-and-play architecture for neuromorphic computing components that can be mixed and matched to create custom applications across domains including vision, audio, robotics, and industrial monitoring.

## Architecture Overview

Functional modules are self-contained, reusable components that implement specific neuromorphic computing functions. The architecture provides:

- **Modular Design**: Each module encapsulates a specific function with clear interfaces
- **Composable**: Modules can be chained together to create complex processing pipelines
- **Type-Safe**: Strong typing and capability declarations ensure compatibility
- **Configurable**: Runtime parameter adjustment and metadata-driven operation
- **Extensible**: Easy to add new module types and implementations

## Module Types

### Base Classes

| Module Type | Purpose | Example Use Cases |
|-------------|---------|-------------------|
| `ProcessingModule` | Data filtering and preprocessing | Noise reduction, temporal smoothing |
| `SensorModule` | Sensor data acquisition | Camera input, IMU reading |
| `AlgorithmModule` | Detection and classification | Anomaly detection, pattern recognition |
| `ControlModule` | Feedback and regulation | PID control, adaptive filtering |
| `FusionModule` | Multi-sensor integration | Kalman filtering, sensor fusion |
| `GenerativeModule` | Data synthesis | Simulation, data augmentation |
| `TransformModule` | Data conversion | Normalization, feature extraction |

### Concrete Implementations

#### Detection Modules (`detection_modules.py`)
- **`AnomalyDetector`**: Statistical anomaly detection in event streams
- **`PatternClassifier`**: Pattern classification based on temporal-spatial features
- **`MotionDetector`**: Motion vector calculation from event-based cameras

#### Processing Modules (`processing_modules.py`)
- **`TemporalFilter`**: Temporal smoothing and filtering operations
- **`SpatialFilter`**: Spatial neighborhood operations and filtering
- **`DataNormalizer`**: Amplitude and coordinate normalization
- **`FeatureExtractor`**: Statistical and structural feature extraction

#### Generic Modules (`generic_modules.py`)
- **`EventBuffer`**: Thread-safe event buffering with configurable size limits and overflow handling
- **`EventRouter`**: Conditional event routing based on metadata, coordinates, or computed features
- **`EventMultiplexer`**: Merging multiple event streams with timestamp synchronization
- **`PerformanceMonitor`**: Real-time performance tracking and alerting for processing pipelines
- **`ConditionalProcessor`**: Dynamic processing logic based on runtime conditions and state
- **`StateManager`**: Persistent state storage across processing cycles with thread-safe operations
- **`DataValidator`**: Schema and constraint validation with multiple rule types and strict mode
- **`EventLogger`**: Structured audit trails and event logging with configurable detail levels
- **`LoadBalancer`**: Multi-strategy load distribution (round-robin, least-loaded, hash-based)
- **`CircuitBreaker`**: Fault tolerance with configurable failure thresholds and recovery logic
- **`RetryHandler`**: Configurable retry logic with exponential backoff and custom strategies
- **`RateLimiter`**: Token bucket rate limiting with per-source capacity management
- **`CacheManager`**: Intelligent caching with TTL and LRU eviction policies

#### Example Modules (`example_module.py`)
- **`EventFilterModule`**: Basic event filtering by amplitude threshold

## Usage Examples

### Basic Module Usage

```python
from eventflow_modules.functions import EventFilterModule

# Create and configure module
config = {
    'name': 'event_filter',
    'threshold': 0.7
}
filter_module = EventFilterModule(config)

# Process data
sample_events = [
    {'timestamp': 1000, 'x': 10, 'y': 20, 'amplitude': 0.3},
    {'timestamp': 1001, 'x': 15, 'y': 25, 'amplitude': 0.8},
]
result = filter_module.process({'events': sample_events})
print(f"Filtered {result['filtered_count']} events")
```

### Module Composition

```python
from eventflow_modules.functions import (
    functional_registry, register_functional_module,
    TemporalFilter, AnomalyDetector
)

# Create pipeline modules
temporal_filter = TemporalFilter({'name': 'temp_filter', 'window_size': 10})
anomaly_detector = AnomalyDetector({'name': 'anomaly_det', 'threshold': 2.0})

# Register modules
register_functional_module(temporal_filter)
register_functional_module(anomaly_detector)

# Check compatibility
pipeline = functional_registry.compose(['temp_filter', 'anomaly_det'])
if pipeline:
    print("Pipeline compatible - ready for processing")
```

### Registry Operations

```python
from eventflow_modules.functions import functional_registry

# Find modules by capability
real_time_modules = functional_registry.find_modules_by_capability(
    real_time_required=True,
    max_latency_ms=50.0
)

# Validate module capabilities
validation = functional_registry.validate_module_capabilities(
    module=my_module,
    backend='cpu-sim'
)
```

## Module Configuration

Modules accept configuration dictionaries with the following common parameters:

- `name`: Module identifier (string)
- `version`: Module version (string, default: "1.0.0")
- Custom parameters specific to each module implementation

### Example Configurations

```python
# Temporal filter configuration
temporal_config = {
    'name': 'temporal_smooth',
    'filter_type': 'gaussian',  # 'mean', 'median', 'gaussian'
    'window_size': 15
}

# Anomaly detector configuration
anomaly_config = {
    'name': 'stat_anomaly',
    'threshold': 2.5,  # Standard deviations
    'window_size': 100
}

# Feature extractor configuration
feature_config = {
    'name': 'feature_ext',
    'feature_types': ['statistical', 'temporal', 'spatial']
}

# EventBuffer configuration
buffer_config = {
    'name': 'event_buffer',
    'buffer_size': 1000,
    'overflow_policy': 'discard_oldest',  # 'discard_oldest', 'discard_newest', 'block'
    'timestamp_sync': True
}

# EventRouter configuration
router_config = {
    'name': 'event_router',
    'routing_rules': [
        {
            'condition': 'coordinates.x > 640',
            'output_stream': 'right_half'
        },
        {
            'condition': 'metadata.source == "camera_left"',
            'output_stream': 'left_camera'
        }
    ],
    'default_stream': 'unrouted'
}

# EventMultiplexer configuration
multiplexer_config = {
    'name': 'event_mux',
    'input_streams': ['camera1', 'camera2', 'imu'],
    'sync_mode': 'timestamp_merge',  # 'timestamp_merge', 'sequential', 'parallel'
    'merge_window_ms': 10.0
}

# PerformanceMonitor configuration
monitor_config = {
    'name': 'perf_monitor',
    'metrics': ['throughput', 'latency', 'memory_usage'],
    'alert_thresholds': {
        'latency_ms': 100,
        'memory_mb': 512
    },
    'log_interval_seconds': 60
}

# ConditionalProcessor configuration
conditional_config = {
    'name': 'conditional_proc',
    'conditions': [
        {
            'rule': 'event_count > 100',
            'action': 'increase_processing_intensity'
        },
        {
            'rule': 'latency > 50ms',
            'action': 'reduce_processing_load'
        }
    ],
    'default_behavior': 'normal_processing'
}
```

## Data Formats

Modules declare supported input/output formats:

- `EVENT_TENSOR`: Event-based data with timestamps and coordinates
- `NUMPY_ARRAY`: Numerical arrays for traditional ML
- `PANDAS_DF`: Tabular data with named columns
- `CUSTOM`: Module-specific custom formats

## Error Handling

The architecture provides comprehensive error handling:

```python
from eventflow_modules.functions import (
    FunctionalModuleError,
    ModuleConfigurationError,
    ModuleInitializationError,
    ModuleExecutionError
)

try:
    module = MyModule(config)
    result = module.process(data)
except ModuleConfigurationError as e:
    print(f"Configuration error: {e}")
except ModuleInitializationError as e:
    print(f"Initialization error: {e}")
except ModuleExecutionError as e:
    print(f"Execution error: {e}")
```

## Performance Considerations

### Latency and Throughput
- Modules declare maximum latency in milliseconds
- Real-time capability is explicitly stated
- Memory usage is tracked and declared

### Capability Validation
```python
# Check if module meets requirements
validation = registry.validate_module_capabilities(
    module=my_module,
    backend='gpu-sim'
)

if not validation['valid']:
    for issue in validation['issues']:
        print(f"Issue: {issue['message']}")
```

## Generic Module Cookbook

The generic modules provide essential infrastructure components for building complex event processing pipelines. Here are detailed usage patterns and integration examples:

### EventBuffer Usage Patterns

**Real-time Stream Smoothing:**
```python
from eventflow_modules.functions import EventBuffer

# Smooth bursty event streams
smoothing_buffer = EventBuffer({
    'name': 'stream_smoother',
    'buffer_size': 100,
    'overflow_policy': 'discard_oldest',
    'timestamp_sync': True
})

# Buffer maintains temporal ordering
events = smoothing_buffer.process({'events': bursty_events})
```

**Memory-Limited Processing:**
```python
# Prevent memory overflow in constrained environments
memory_safe_buffer = EventBuffer({
    'name': 'memory_guard',
    'buffer_size': 512,  # Fixed memory footprint
    'overflow_policy': 'block',  # Wait for processing
    'timestamp_sync': False  # Speed over precision
})
```

### EventRouter Integration Examples

**Multi-Camera Processing:**
```python
from eventflow_modules.functions import EventRouter

# Route events by camera quadrant
quadrant_router = EventRouter({
    'name': 'camera_router',
    'routing_rules': [
        {'condition': 'coordinates.x < 640 and coordinates.y < 480', 'output_stream': 'quadrant_1'},
        {'condition': 'coordinates.x >= 640 and coordinates.y < 480', 'output_stream': 'quadrant_2'},
        {'condition': 'coordinates.x < 640 and coordinates.y >= 480', 'output_stream': 'quadrant_3'},
        {'condition': 'coordinates.x >= 640 and coordinates.y >= 480', 'output_stream': 'quadrant_4'}
    ],
    'default_stream': 'unassigned'
})
```

**Sensor Data Classification:**
```python
# Route by sensor type and priority
sensor_router = EventRouter({
    'name': 'sensor_classifier',
    'routing_rules': [
        {'condition': 'metadata.priority == "critical"', 'output_stream': 'urgent'},
        {'condition': 'metadata.sensor_type == "imu"', 'output_stream': 'motion_data'},
        {'condition': 'metadata.sensor_type == "camera"', 'output_stream': 'vision_data'}
    ]
})
```

### EventMultiplexer Synchronization

**Multi-Sensor Fusion:**
```python
from eventflow_modules.functions import EventMultiplexer

# Synchronize camera and IMU data
fusion_mux = EventMultiplexer({
    'name': 'sensor_fusion',
    'input_streams': ['stereo_camera_left', 'stereo_camera_right', 'imu'],
    'sync_mode': 'timestamp_merge',
    'merge_window_ms': 5.0  # 5ms synchronization window
})

# Output: temporally aligned event streams
fused_data = fusion_mux.process({
    'stereo_camera_left': camera_left_events,
    'stereo_camera_right': camera_right_events,
    'imu': imu_events
})
```

**Parallel Processing Results:**
```python
# Combine results from parallel processors
parallel_mux = EventMultiplexer({
    'name': 'result_aggregator',
    'input_streams': ['processor_1', 'processor_2', 'processor_3'],
    'sync_mode': 'parallel',  # No temporal constraints
    'merge_window_ms': 0.0
})
```

### PerformanceMonitor Integration

**Real-time System Monitoring:**
```python
from eventflow_modules.functions import PerformanceMonitor

# Monitor pipeline health
health_monitor = PerformanceMonitor({
    'name': 'pipeline_health',
    'metrics': ['throughput', 'latency', 'memory_usage', 'cpu_usage'],
    'alert_thresholds': {
        'latency_ms': 100,
        'memory_mb': 1024,
        'cpu_percent': 80
    },
    'log_interval_seconds': 30
})

# Integrate into processing pipeline
class MonitoredProcessor:
    def __init__(self, processor, monitor):
        self.processor = processor
        self.monitor = monitor

    def process(self, inputs):
        start_time = time.time()
        self.monitor.record_metric('input_count', len(inputs.get('events', [])))

        result = self.processor.process(inputs)

        latency = (time.time() - start_time) * 1000
        self.monitor.record_metric('latency_ms', latency)
        self.monitor.record_metric('output_count', len(result.get('events', [])))

        return result
```

### ConditionalProcessor Adaptive Behavior

**Load-Adaptive Processing:**
```python
from eventflow_modules.functions import ConditionalProcessor

# Adjust processing based on system load
adaptive_processor = ConditionalProcessor({
    'name': 'load_adaptive',
    'conditions': [
        {
            'rule': 'system_load > 0.8',
            'action': 'reduce_resolution'
        },
        {
            'rule': 'event_rate > 10000',
            'action': 'enable_downsampling'
        },
        {
            'rule': 'memory_usage > 0.9',
            'action': 'trigger_garbage_collection'
        }
    ],
    'default_behavior': 'high_quality_processing'
})
```

## Advanced Pipeline Examples

### Real-time Vision Pipeline with Monitoring

```python
from eventflow_modules.functions import (
    EventBuffer, EventRouter, PerformanceMonitor,
    TemporalFilter, MotionDetector
)

# Build monitored vision processing pipeline
def create_vision_pipeline():
    components = {}

    # Input buffering for stream stability
    components['input_buffer'] = EventBuffer({
        'name': 'vision_buffer',
        'buffer_size': 500,
        'overflow_policy': 'discard_oldest'
    })

    # Performance monitoring
    components['monitor'] = PerformanceMonitor({
        'name': 'vision_monitor',
        'metrics': ['throughput', 'latency'],
        'alert_thresholds': {'latency_ms': 50}
    })

    # Processing modules
    components['temporal_filter'] = TemporalFilter({
        'name': 'motion_filter',
        'filter_type': 'gaussian',
        'window_size': 10
    })

    components['motion_detector'] = MotionDetector({
        'name': 'motion_analysis',
        'sensitivity': 0.3
    })

    return components

# Usage
pipeline = create_vision_pipeline()
camera_events = capture_camera_events()

# Process through pipeline
buffered = pipeline['input_buffer'].process({'events': camera_events})
filtered = pipeline['temporal_filter'].process(buffered)
motion_events = pipeline['motion_detector'].process(filtered)

# Monitor performance
pipeline['monitor'].record_metric('events_processed', len(motion_events.get('events', [])))
```

### Robotics Control Pipeline

```python
from eventflow_modules.functions import (
    EventMultiplexer, EventRouter, ConditionalProcessor,
    ObstacleAvoidanceController, PathPlanner
)

def create_robotics_pipeline():
    components = {}

    # Multi-sensor fusion
    components['sensor_fusion'] = EventMultiplexer({
        'name': 'robot_sensors',
        'input_streams': ['lidar', 'camera', 'imu'],
        'sync_mode': 'timestamp_merge',
        'merge_window_ms': 10.0
    })

    # Conditional processing based on environment
    components['environment_adapter'] = ConditionalProcessor({
        'name': 'adaptive_control',
        'conditions': [
            {'rule': 'obstacle_density > 0.7', 'action': 'enable_avoidance_mode'},
            {'rule': 'speed > 2.0', 'action': 'reduce_safety_margin'}
        ]
    })

    # Control modules
    components['path_planner'] = PathPlanner({
        'name': 'navigation',
        'algorithm': 'astar',
        'safety_margin': 0.5
    })

    components['obstacle_avoidance'] = ObstacleAvoidanceController({
        'name': 'collision_prevention',
        'reaction_distance': 2.0
    })

    return components

# Real-time robotics processing
robot_pipeline = create_robotics_pipeline()
sensor_data = collect_sensor_data()

fused_sensors = robot_pipeline['sensor_fusion'].process(sensor_data)
adapted_processing = robot_pipeline['environment_adapter'].process(fused_sensors)

path = robot_pipeline['path_planner'].process(adapted_processing)
safe_commands = robot_pipeline['obstacle_avoidance'].process(path)
```

## Extending the Architecture

### Creating New Module Types

```python
from eventflow_modules.functions import FunctionalModule, ModuleType

class CustomModuleType(FunctionalModule):
    def _declare_capabilities(self):
        return super()._declare_capabilities()

    def _declare_requirements(self):
        return super()._declare_requirements()

    def process(self, inputs):
        # Custom processing logic
        return processed_data
```

### Adding New Module Implementations

```python
from eventflow_modules.functions import AlgorithmModule

class MyCustomDetector(AlgorithmModule):
    def process(self, inputs):
        # Implement custom detection logic
        return detection_results
```

## Best Practices

1. **Capability Declaration**: Always declare accurate capabilities and requirements
2. **Error Handling**: Use proper exception types for different error conditions
3. **Documentation**: Document module behavior, parameters, and data formats
4. **Validation**: Implement input/output validation for robustness
5. **Performance**: Profile and declare realistic latency/memory requirements
6. **Composition**: Design modules to work well in pipelines

## Integration with EventFlow Core

Functional modules integrate seamlessly with the EventFlow core runtime:

- Modules can be used in EIR graphs as processing nodes
- Backend compatibility is automatically validated
- Configuration can be serialized with EIR definitions
- Performance monitoring integrates with EventFlow profiling tools

This architecture enables rapid development of neuromorphic applications by providing reusable, well-tested components that can be composed like building blocks.

## Domain-Specific Module Recipe Book

This section provides comprehensive recipes for using domain-specific functional modules in real-world neuromorphic applications.

### Vision Processing Recipes

#### Real-Time Object Tracking Pipeline

```python
from eventflow_modules.functions import (
    OpticalFlowEstimator, CornerDetector, ObjectTracker,
    EventBuffer, PerformanceMonitor
)

def create_object_tracking_pipeline():
    """Create a complete object tracking pipeline for event-based cameras."""

    # Input buffering for temporal smoothing
    buffer = EventBuffer({
        'name': 'tracking_buffer',
        'buffer_size': 200,
        'overflow_policy': 'discard_oldest'
    })

    # Feature extraction
    corner_detector = CornerDetector({
        'name': 'corner_detector',
        'threshold': 0.7,
        'min_distance': 5,
        'max_corners': 100
    })

    # Motion estimation
    flow_estimator = OpticalFlowEstimator({
        'name': 'flow_estimator',
        'flow_method': 'lucas_kanade',
        'search_radius': 7,
        'temporal_window': 3
    })

    # Object tracking
    tracker = ObjectTracker({
        'name': 'object_tracker',
        'tracking_method': 'kalman_filter',
        'max_objects': 10,
        'min_track_length': 5
    })

    # Performance monitoring
    monitor = PerformanceMonitor({
        'name': 'tracking_monitor',
        'metrics': ['throughput', 'latency', 'memory_usage'],
        'alert_thresholds': {'latency_ms': 50}
    })

    return [buffer, corner_detector, flow_estimator, tracker, monitor]

# Usage
pipeline = create_object_tracking_pipeline()
camera_events = capture_event_camera_data()

# Process through pipeline
for module in pipeline:
    camera_events = module.process(camera_events)

tracked_objects = camera_events.get('tracked_objects', [])
print(f"Tracked {len(tracked_objects)} objects")
```

#### Multi-Camera SLAM System

```python
from eventflow_modules.functions import (
    OpticalFlowEstimator, MotionDetector,
    EventMultiplexer, EventRouter
)

def create_slam_pipeline():
    """Create SLAM pipeline for multiple event-based cameras."""

    # Multi-camera synchronization
    synchronizer = EventMultiplexer({
        'name': 'camera_sync',
        'input_streams': ['camera_front', 'camera_left', 'camera_right'],
        'sync_mode': 'timestamp_merge',
        'merge_window_ms': 2.0
    })

    # Motion detection for each camera
    motion_detectors = {}
    for camera in ['front', 'left', 'right']:
        motion_detectors[camera] = MotionDetector({
            'name': f'motion_{camera}',
            'sensitivity': 0.3,
            'min_motion_pixels': 50
        })

    # Optical flow for feature tracking
    flow_estimator = OpticalFlowEstimator({
        'name': 'slam_flow',
        'flow_method': 'farneback',
        'pyramid_levels': 3
    })

    return synchronizer, motion_detectors, flow_estimator

# Process multi-camera SLAM
synchronizer, motion_detectors, flow_estimator = create_slam_pipeline()

camera_streams = {
    'camera_front': front_events,
    'camera_left': left_events,
    'camera_right': right_events
}

# Synchronize and process
synced_data = synchronizer.process(camera_streams)
motion_results = {}

for camera, detector in motion_detectors.items():
    motion_results[camera] = detector.process(synced_data[camera])

# Estimate 3D motion
flow_result = flow_estimator.process(synced_data)
```

### Audio Processing Recipes

#### Voice Activity Detection and Keyword Spotting

```python
from eventflow_modules.functions import (
    VoiceActivityDetector, KeywordSpotter, AudioBeamformer,
    EventBuffer, DataValidator
)

def create_audio_processing_pipeline():
    """Create audio processing pipeline for voice interaction."""

    # Input validation and buffering
    validator = DataValidator({
        'name': 'audio_validator',
        'validation_rules': [
            {
                'type': 'range',
                'field': 'amplitude',
                'name': 'amplitude_range',
                'min': -1.0,
                'max': 1.0
            }
        ]
    })

    buffer = EventBuffer({
        'name': 'audio_buffer',
        'buffer_size': 1024,
        'overflow_policy': 'discard_oldest'
    })

    # Voice activity detection
    vad = VoiceActivityDetector({
        'name': 'voice_detector',
        'threshold': 0.6,
        'min_duration_ms': 100,
        'max_silence_ms': 500
    })

    # Keyword spotting
    keyword_spotter = KeywordSpotter({
        'name': 'wake_word_detector',
        'keywords': ['hey robot', 'wake up', 'attention'],
        'sensitivity': 0.8,
        'language': 'en-US'
    })

    # Beamforming for noise reduction
    beamformer = AudioBeamformer({
        'name': 'audio_beamformer',
        'num_microphones': 4,
        'beam_width_degrees': 30,
        'target_direction': 0  # Front-facing
    })

    return [validator, buffer, vad, keyword_spotter, beamformer]

# Real-time audio processing
audio_pipeline = create_audio_processing_pipeline()
microphone_events = capture_audio_events()

for module in audio_pipeline:
    microphone_events = module.process(microphone_events)

if microphone_events.get('wake_word_detected'):
    print("Wake word detected - activating voice interface")
```

#### Acoustic Scene Analysis

```python
from eventflow_modules.functions import (
    VoiceActivityDetector, AudioBeamformer,
    EventRouter, PerformanceMonitor
)

def create_scene_analysis_pipeline():
    """Create pipeline for acoustic scene understanding."""

    # Multi-source detection
    vad = VoiceActivityDetector({
        'name': 'multi_source_vad',
        'threshold': 0.5,
        'max_sources': 3,
        'separation_angle_degrees': 45
    })

    # Directional beamforming
    beamformer = AudioBeamformer({
        'name': 'directional_beamformer',
        'num_microphones': 8,
        'beam_width_degrees': 20,
        'adaptive_beams': True
    })

    # Source routing
    router = EventRouter({
        'name': 'source_router',
        'routing_rules': [
            {
                'condition': 'direction < -45',
                'output_stream': 'left_sources'
            },
            {
                'condition': 'direction > 45',
                'output_stream': 'right_sources'
            }
        ],
        'default_stream': 'center_sources'
    })

    # Performance monitoring
    monitor = PerformanceMonitor({
        'name': 'audio_monitor',
        'metrics': ['throughput', 'latency', 'cpu_usage'],
        'alert_thresholds': {'latency_ms': 20, 'cpu_percent': 70}
    })

    return vad, beamformer, router, monitor

# Analyze acoustic scene
scene_pipeline = create_scene_analysis_pipeline()
audio_scene = capture_multi_channel_audio()

vad_result = scene_pipeline[0].process(audio_scene)
beamformed = scene_pipeline[1].process(vad_result)
routed_sources = scene_pipeline[2].process(beamformed)
scene_pipeline[3].process(routed_sources)  # Monitor performance
```

### Robotics Control Recipes

#### Autonomous Navigation with Obstacle Avoidance

```python
from eventflow_modules.functions import (
    ObstacleAvoidanceController, PathPlanner, MotorController,
    EventMultiplexer, StateManager
)

def create_navigation_pipeline():
    """Create autonomous navigation pipeline for mobile robot."""

    # Sensor fusion
    sensor_fusion = EventMultiplexer({
        'name': 'robot_sensors',
        'input_streams': ['lidar', 'radar', 'imu', 'camera'],
        'sync_mode': 'timestamp_merge',
        'merge_window_ms': 10.0
    })

    # State management
    state_manager = StateManager({
        'name': 'robot_state',
        'operation': 'update',
        'state_key': 'navigation'
    })

    # Path planning
    path_planner = PathPlanner({
        'name': 'global_planner',
        'algorithm': 'astar',
        'grid_resolution': 0.1,
        'safety_margin': 0.3,
        'max_planning_time_ms': 100
    })

    # Obstacle avoidance
    obstacle_avoidance = ObstacleAvoidanceController({
        'name': 'local_avoidance',
        'detection_range': 3.0,
        'reaction_distance': 1.5,
        'max_turn_rate': 45.0
    })

    # Motor control
    motor_controller = MotorController({
        'name': 'drive_controller',
        'control_mode': 'velocity',
        'max_linear_velocity': 1.0,
        'max_angular_velocity': 90.0,
        'pid_gains': {'kp': 1.2, 'ki': 0.1, 'kd': 0.05}
    })

    return [sensor_fusion, state_manager, path_planner, obstacle_avoidance, motor_controller]

# Autonomous navigation
nav_pipeline = create_navigation_pipeline()
goal_position = {'x': 10.0, 'y': 5.0, 'theta': 0.0}

# Initial path planning
sensor_data = collect_robot_sensors()
fused_data = nav_pipeline[0].process(sensor_data)

path_plan = nav_pipeline[2].process({
    **fused_data,
    'goal': goal_position,
    'current_pose': get_robot_pose()
})

# Real-time obstacle avoidance and control
for sensor_update in real_time_sensor_stream():
    fused_update = nav_pipeline[0].process(sensor_update)

    # Update robot state
    nav_pipeline[1].process(fused_update)

    # Local obstacle avoidance
    safe_commands = nav_pipeline[3].process(fused_update)

    # Motor control execution
    motor_commands = nav_pipeline[4].process(safe_commands)

    execute_motor_commands(motor_commands)
```

#### Robotic Manipulation with Force Control

```python
from eventflow_modules.functions import (
    MotorController, ConditionalProcessor,
    EventBuffer, PerformanceMonitor
)

def create_manipulation_pipeline():
    """Create robotic manipulation pipeline with force control."""

    # Force/torque sensor buffering
    force_buffer = EventBuffer({
        'name': 'force_buffer',
        'buffer_size': 50,
        'overflow_policy': 'discard_oldest'
    })

    # Adaptive control based on force feedback
    force_controller = ConditionalProcessor({
        'name': 'force_adaptive',
        'conditions': [
            {
                'rule': 'force_z > 50',  # High contact force
                'action': 'reduce_force'
            },
            {
                'rule': 'force_z < 5',   # Light contact
                'action': 'increase_force'
            },
            {
                'rule': 'slipping_detected',
                'action': 'adjust_grip'
            }
        ],
        'default_behavior': 'maintain_force'
    })

    # Precision motor control
    motor_controller = MotorController({
        'name': 'manipulator_controller',
        'control_mode': 'impedance',
        'stiffness': {'x': 1000, 'y': 1000, 'z': 500},
        'damping': {'x': 50, 'y': 50, 'z': 25},
        'force_limits': {'max': 100, 'min': 1}
    })

    # Performance monitoring
    performance_monitor = PerformanceMonitor({
        'name': 'manipulation_monitor',
        'metrics': ['position_error', 'force_error', 'settling_time'],
        'alert_thresholds': {'position_error': 0.01, 'force_error': 5.0}
    })

    return [force_buffer, force_controller, motor_controller, performance_monitor]

# Precision manipulation
manip_pipeline = create_manipulation_pipeline()
target_pose = {'x': 0.5, 'y': 0.2, 'z': 0.1, 'force': 20.0}

# Execute manipulation with force control
for force_reading in real_time_force_feedback():
    buffered_force = manip_pipeline[0].process(force_reading)
    adapted_control = manip_pipeline[1].process({
        **buffered_force,
        'target_pose': target_pose
    })
    motor_commands = manip_pipeline[2].process(adapted_control)
    manip_pipeline[3].process(motor_commands)  # Monitor performance

    if manip_pipeline[3].has_alerts():
        adjust_manipulation_strategy()
```

### Detection and Classification Recipes

#### Anomaly Detection in Industrial Monitoring

```python
from eventflow_modules.functions import (
    AnomalyDetector, PatternClassifier, MotionDetector,
    EventMultiplexer, EventLogger
)

def create_industrial_monitoring_pipeline():
    """Create anomaly detection pipeline for industrial equipment."""

    # Multi-sensor data fusion
    sensor_fusion = EventMultiplexer({
        'name': 'equipment_sensors',
        'input_streams': ['vibration', 'current', 'temperature', 'pressure'],
        'sync_mode': 'timestamp_merge',
        'merge_window_ms': 100.0
    })

    # Statistical anomaly detection
    statistical_anomaly = AnomalyDetector({
        'name': 'statistical_monitor',
        'method': 'z_score',
        'threshold': 3.0,
        'window_size': 1000,
        'features': ['mean', 'std', 'rms', 'peak']
    })

    # Pattern-based classification
    pattern_classifier = PatternClassifier({
        'name': 'fault_classifier',
        'method': 'svm',
        'features': ['frequency_domain', 'time_domain', 'wavelet'],
        'classes': ['normal', 'bearing_wear', 'imbalance', 'misalignment']
    })

    # Motion anomaly detection (for rotating equipment)
    motion_detector = MotionDetector({
        'name': 'rotation_monitor',
        'expected_rpm': 1800,
        'rpm_tolerance': 50,
        'phase_lock_required': True
    })

    # Audit logging
    audit_logger = EventLogger({
        'name': 'anomaly_logger',
        'log_events': ['anomaly_detected', 'classification_changed'],
        'include_metrics': True
    })

    return [sensor_fusion, statistical_anomaly, pattern_classifier, motion_detector, audit_logger]

# Industrial equipment monitoring
monitoring_pipeline = create_industrial_monitoring_pipeline()
equipment_sensors = collect_industrial_sensor_data()

for module in monitoring_pipeline:
    equipment_sensors = module.process(equipment_sensors)

if equipment_sensors.get('anomaly_detected'):
    fault_type = equipment_sensors.get('predicted_class', 'unknown')
    trigger_maintenance_alert(fault_type)
```

#### Multi-Class Event Classification

```python
from eventflow_modules.functions import (
    PatternClassifier, FeatureExtractor,
    DataValidator, EventRouter
)

def create_classification_pipeline():
    """Create multi-class event classification pipeline."""

    # Input validation
    validator = DataValidator({
        'name': 'input_validator',
        'validation_rules': [
            {
                'type': 'schema',
                'name': 'event_schema',
                'required_fields': ['timestamp', 'features'],
                'field_types': {'timestamp': float}
            }
        ]
    })

    # Feature extraction
    feature_extractor = FeatureExtractor({
        'name': 'feature_engineering',
        'extraction_methods': ['statistical', 'temporal', 'spectral'],
        'normalization': 'z_score',
        'feature_selection': 'mutual_info'
    })

    # Pattern classification
    classifier = PatternClassifier({
        'name': 'multi_class_classifier',
        'method': 'random_forest',
        'num_classes': 5,
        'class_names': ['class_a', 'class_b', 'class_c', 'class_d', 'unknown'],
        'confidence_threshold': 0.8
    })

    # Classification routing
    result_router = EventRouter({
        'name': 'classification_router',
        'routing_rules': [
            {
                'condition': 'confidence > 0.9',
                'output_stream': 'high_confidence'
            },
            {
                'condition': 'predicted_class == "unknown"',
                'output_stream': 'needs_review'
            }
        ],
        'default_stream': 'standard_results'
    })

    return [validator, feature_extractor, classifier, result_router]

# Multi-class classification
classification_pipeline = create_classification_pipeline()
input_events = load_classification_dataset()

for module in classification_pipeline:
    input_events = module.process(input_events)

# Route results based on confidence and class
high_confidence = input_events.get('high_confidence', [])
needs_review = input_events.get('needs_review', [])

print(f"High confidence classifications: {len(high_confidence)}")
print(f"Items needing review: {len(needs_review)}")
```

### Processing Module Recipes

#### Real-Time Signal Processing Chain

```python
from eventflow_modules.functions import (
    TemporalFilter, SpatialFilter, DataNormalizer,
    EventBuffer, PerformanceMonitor
)

def create_signal_processing_pipeline():
    """Create real-time signal processing pipeline."""

    # Input buffering
    buffer = EventBuffer({
        'name': 'signal_buffer',
        'buffer_size': 512,
        'overflow_policy': 'discard_oldest'
    })

    # Temporal filtering
    temporal_filter = TemporalFilter({
        'name': 'temporal_smoothing',
        'filter_type': 'butterworth',
        'order': 4,
        'cutoff_frequency': 50.0,
        'sampling_rate': 1000.0
    })

    # Spatial filtering (if applicable)
    spatial_filter = SpatialFilter({
        'name': 'spatial_denoising',
        'filter_type': 'median',
        'kernel_size': 3,
        'neighborhood_type': 'moore'
    })

    # Data normalization
    normalizer = DataNormalizer({
        'name': 'signal_normalizer',
        'normalization_method': 'min_max',
        'feature_range': [-1.0, 1.0],
        'clip_outliers': True,
        'outlier_percentile': 99.0
    })

    # Performance monitoring
    monitor = PerformanceMonitor({
        'name': 'processing_monitor',
        'metrics': ['latency', 'throughput', 'memory_usage'],
        'alert_thresholds': {'latency_ms': 10}
    })

    return [buffer, temporal_filter, spatial_filter, normalizer, monitor]

# Real-time signal processing
processing_pipeline = create_signal_processing_pipeline()
raw_signals = capture_sensor_signals()

processed_signals = raw_signals
for module in processing_pipeline:
    processed_signals = module.process(processed_signals)

# Check processing performance
if processing_pipeline[-1].has_alerts():
    print("Processing performance degraded - consider optimization")
```

#### Adaptive Feature Extraction

```python
from eventflow_modules.functions import (
    FeatureExtractor, ConditionalProcessor,
    DataValidator, StateManager
)

def create_adaptive_feature_pipeline():
    """Create adaptive feature extraction pipeline."""

    # Input validation
    validator = DataValidator({
        'name': 'feature_validator',
        'validation_rules': [
            {
                'type': 'range',
                'name': 'amplitude_check',
                'field': 'amplitude',
                'min': -10.0,
                'max': 10.0
            }
        ]
    })

    # State management for adaptation
    state_manager = StateManager({
        'name': 'feature_state',
        'state_key': 'extraction_params'
    })

    # Adaptive feature extraction
    adaptive_extractor = ConditionalProcessor({
        'name': 'adaptive_features',
        'conditions': [
            {
                'rule': 'signal_type == "periodic"',
                'action': 'use_frequency_features'
            },
            {
                'rule': 'signal_type == "transient"',
                'action': 'use_wavelet_features'
            },
            {
                'rule': 'noise_level > 0.5',
                'action': 'use_robust_features'
            }
        ],
        'default_behavior': 'use_statistical_features'
    })

    # Feature extraction
    feature_extractor = FeatureExtractor({
        'name': 'multi_modal_features',
        'extraction_methods': ['statistical', 'temporal', 'spectral'],
        'dimensionality_reduction': 'pca',
        'n_components': 10
    })

    return [validator, state_manager, adaptive_extractor, feature_extractor]

# Adaptive feature extraction
feature_pipeline = create_adaptive_feature_pipeline()
input_signals = load_diverse_signal_data()

for module in feature_pipeline:
    input_signals = module.process(input_signals)

extracted_features = input_signals.get('features', [])
print(f"Extracted {len(extracted_features)} feature vectors")
```

## Module Compatibility Matrix

| Module Type | CPU Backend | GPU Backend | Real-time Capable | Memory Efficient |
|-------------|-------------|-------------|-------------------|------------------|
| EventBuffer | ✅ | ✅ | ✅ | ✅ |
| EventRouter | ✅ | ✅ | ✅ | ✅ |
| EventMultiplexer | ✅ | ⚠️ | ⚠️ | ✅ |
| PerformanceMonitor | ✅ | ✅ | ✅ | ✅ |
| ConditionalProcessor | ✅ | ⚠️ | ✅ | ✅ |
| StateManager | ✅ | ⚠️ | ✅ | ✅ |
| DataValidator | ✅ | ✅ | ✅ | ✅ |
| EventLogger | ✅ | ⚠️ | ⚠️ | ✅ |
| LoadBalancer | ✅ | ⚠️ | ✅ | ✅ |
| CircuitBreaker | ✅ | ✅ | ✅ | ✅ |
| RetryHandler | ✅ | ✅ | ⚠️ | ✅ |
| RateLimiter | ✅ | ✅ | ✅ | ✅ |
| CacheManager | ✅ | ⚠️ | ✅ | ⚠️ |
| OpticalFlowEstimator | ✅ | ✅ | ⚠️ | ⚠️ |
| CornerDetector | ✅ | ✅ | ✅ | ✅ |
| ObjectTracker | ✅ | ✅ | ⚠️ | ⚠️ |
| VoiceActivityDetector | ✅ | ✅ | ✅ | ✅ |
| KeywordSpotter | ✅ | ⚠️ | ⚠️ | ⚠️ |
| AudioBeamformer | ✅ | ✅ | ⚠️ | ⚠️ |
| ObstacleAvoidanceController | ✅ | ✅ | ✅ | ✅ |
| PathPlanner | ✅ | ⚠️ | ⚠️ | ⚠️ |
| MotorController | ✅ | ✅ | ✅ | ✅ |
| AnomalyDetector | ✅ | ✅ | ✅ | ✅ |
| PatternClassifier | ✅ | ✅ | ⚠️ | ⚠️ |
| MotionDetector | ✅ | ✅ | ✅ | ✅ |
| TemporalFilter | ✅ | ✅ | ✅ | ✅ |
| SpatialFilter | ✅ | ✅ | ⚠️ | ⚠️ |
| DataNormalizer | ✅ | ✅ | ✅ | ✅ |
| FeatureExtractor | ✅ | ✅ | ⚠️ | ⚠️ |

**Legend:**
- ✅ Full support
- ⚠️ Limited support or performance considerations
- ❌ Not supported

## Best Practices for Production Deployments

1. **Resource Management**: Always configure buffer sizes and timeouts appropriate for your target hardware
2. **Error Handling**: Implement comprehensive error handling and fallback strategies
3. **Monitoring**: Use PerformanceMonitor in all production pipelines
4. **Validation**: Enable DataValidator for all external data sources
5. **Logging**: Configure EventLogger for debugging and compliance
6. **Load Balancing**: Use LoadBalancer for multi-instance deployments
7. **Circuit Breakers**: Implement CircuitBreaker for fault-tolerant systems
8. **State Management**: Use StateManager for modules requiring context
9. **Conditional Processing**: Leverage ConditionalProcessor for adaptive behavior
10. **Testing**: Validate all module combinations in your target environment

## Advanced Infrastructure Recipes

This section covers enterprise-grade infrastructure patterns using the advanced generic modules for production deployments.

### Fault-Tolerant Processing with Retry and Circuit Breaker

```python
from eventflow_modules.functions import (
    RetryHandler, CircuitBreaker, EventLogger,
    PerformanceMonitor, DataValidator
)

def create_fault_tolerant_pipeline():
    """Create a production-ready fault-tolerant processing pipeline."""

    # Input validation with strict mode
    validator = DataValidator({
        'name': 'strict_validator',
        'validation_rules': [
            {
                'type': 'schema',
                'name': 'api_schema',
                'required_fields': ['request_id', 'data', 'timestamp'],
                'field_types': {'request_id': str, 'timestamp': float}
            },
            {
                'type': 'range',
                'name': 'data_range',
                'field': 'data.value',
                'min': 0.0,
                'max': 100.0
            }
        ],
        'strict_mode': True  # Fail on validation errors
    })

    # Circuit breaker to prevent cascade failures
    circuit_breaker = CircuitBreaker({
        'name': 'api_circuit_breaker',
        'failure_threshold': 5,
        'recovery_timeout': 60.0,
        'success_threshold': 3
    })

    # Retry handler for transient failures
    retry_handler = RetryHandler({
        'name': 'api_retry_handler',
        'max_retries': 3,
        'base_delay_ms': 500,
        'max_delay_ms': 5000,
        'backoff_strategy': 'exponential',
        'retry_condition': 'error_code',
        'retry_error_codes': [500, 502, 503, 504, 408, 429]
    })

    # Comprehensive logging
    audit_logger = EventLogger({
        'name': 'production_audit',
        'log_events': ['processing_start', 'processing_end', 'error', 'retry'],
        'include_metrics': True
    })

    # Performance monitoring with alerts
    performance_monitor = PerformanceMonitor({
        'name': 'production_monitor',
        'metrics': ['throughput', 'latency', 'error_rate'],
        'alert_thresholds': {
            'latency_ms': 1000,
            'error_rate_percent': 5.0
        }
    })

    return [validator, circuit_breaker, retry_handler, audit_logger, performance_monitor]

# Production API processing with full fault tolerance
fault_tolerant_pipeline = create_fault_tolerant_pipeline()

def process_api_request(request_data):
    """Process API requests with comprehensive fault tolerance."""
    try:
        result = request_data
        for module in fault_tolerant_pipeline:
            result = module.process(result)

            # Check for circuit breaker state
            if isinstance(result, dict) and result.get('circuit_breaker'):
                if result['circuit_breaker']['state'] == 'open':
                    return {
                        'status': 'service_unavailable',
                        'retry_after': result['circuit_breaker']['last_failure_time'] + 60,
                        'error': 'Circuit breaker is open'
                    }

            # Check for retry scheduling
            if isinstance(result, dict) and result.get('retry', {}).get('scheduled'):
                # Schedule retry (in real implementation, use task queue)
                schedule_retry(result, result['retry']['delay_ms'])
                return {
                    'status': 'retry_scheduled',
                    'retry_at': result['retry']['next_retry_at']
                }

        return result

    except Exception as e:
        # Log critical errors
        fault_tolerant_pipeline[-1].process({
            'error': str(e),
            'severity': 'critical',
            'component': 'api_processor'
        })
        return {'status': 'internal_error', 'error': 'Processing failed'}
```

### High-Throughput Rate Limiting and Caching

```python
from eventflow_modules.functions import (
    RateLimiter, CacheManager, LoadBalancer,
    StateManager, EventRouter
)

def create_high_throughput_system():
    """Create a high-throughput system with rate limiting and caching."""

    # Multi-tier rate limiting
    api_limiter = RateLimiter({
        'name': 'api_rate_limiter',
        'capacity': 1000,
        'refill_rate_per_second': 100,
        'algorithm': 'token_bucket'
    })

    user_limiter = RateLimiter({
        'name': 'user_rate_limiter',
        'capacity': 100,
        'refill_rate_per_second': 10,
        'key_field': 'user_id'
    })

    # Intelligent caching
    response_cache = CacheManager({
        'name': 'api_response_cache',
        'max_cache_size': 10000,
        'default_ttl_seconds': 300,
        'key_fields': ['endpoint', 'parameters', 'user_id']
    })

    # Load balancing across worker instances
    load_balancer = LoadBalancer({
        'name': 'worker_load_balancer',
        'workers': ['worker_1', 'worker_2', 'worker_3', 'worker_4'],
        'strategy': 'least_loaded'
    })

    # State management for user sessions
    session_manager = StateManager({
        'name': 'user_session_state',
        'operation': 'update',
        'state_key': 'session'
    })

    # Route based on request type and load
    smart_router = EventRouter({
        'name': 'request_router',
        'routing_rules': [
            {
                'condition': 'cached_response_available',
                'output_stream': 'cache_hit'
            },
            {
                'condition': 'high_priority_request',
                'output_stream': 'priority_queue'
            }
        ],
        'default_stream': 'standard_processing'
    })

    return [api_limiter, user_limiter, response_cache, load_balancer, session_manager, smart_router]

# High-throughput request processing
throughput_system = create_high_throughput_system()

def process_high_volume_request(request):
    """Process high-volume requests with rate limiting and caching."""

    # Step 1: Global API rate limiting
    api_check = throughput_system[0].process(request)
    if not api_check.get('rate_limit', {}).get('allowed', True):
        return {
            'status': 'rate_limited',
            'retry_after': api_check['rate_limit']['wait_time_seconds']
        }

    # Step 2: Per-user rate limiting
    user_check = throughput_system[1].process(api_check)
    if not user_check.get('rate_limit', {}).get('allowed', True):
        return {
            'status': 'user_rate_limited',
            'retry_after': user_check['rate_limit']['wait_time_seconds']
        }

    # Step 3: Check cache
    cache_lookup = throughput_system[2].process({
        'cache_operation': 'get',
        'endpoint': request.get('endpoint'),
        'parameters': request.get('parameters'),
        'user_id': request.get('user_id')
    })

    if cache_lookup.get('cache_hit'):
        return {
            'status': 'cache_hit',
            'data': cache_lookup['cached_data'],
            'cache_age': cache_lookup['cache']['age_seconds']
        }

    # Step 4: Load balancing
    worker_assignment = throughput_system[3].process(user_check)

    # Step 5: Update user session
    session_update = throughput_system[4].process({
        'state_key': f"session_{request.get('user_id')}",
        'updates': {
            'last_request': time.time(),
            'request_count': 'increment'
        }
    })

    # Step 6: Smart routing
    final_routing = throughput_system[5].process(session_update)

    # Route to appropriate processing queue
    queue_name = final_routing.get('routing', {}).get('selected_worker', 'standard')
    submit_to_queue(queue_name, final_routing)

    return {'status': 'queued', 'queue': queue_name}
```

### Real-Time Analytics Dashboard with State Management

```python
from eventflow_modules.functions import (
    StateManager, PerformanceMonitor, EventLogger,
    ConditionalProcessor, CacheManager
)

def create_analytics_dashboard():
    """Create a real-time analytics dashboard with state management."""

    # Real-time metrics state
    metrics_state = StateManager({
        'name': 'metrics_aggregator',
        'state_key': 'dashboard_metrics'
    })

    # Performance monitoring with custom metrics
    perf_monitor = PerformanceMonitor({
        'name': 'dashboard_monitor',
        'metrics': ['requests_per_second', 'error_rate', 'response_time_p95'],
        'alert_thresholds': {
            'error_rate_percent': 1.0,
            'response_time_p95_ms': 500
        }
    })

    # Intelligent caching for dashboard data
    dashboard_cache = CacheManager({
        'name': 'dashboard_cache',
        'max_cache_size': 1000,
        'default_ttl_seconds': 30,  # Real-time data
        'key_fields': ['dashboard_id', 'time_range', 'filters']
    })

    # Conditional processing based on load
    adaptive_processor = ConditionalProcessor({
        'name': 'load_adaptive_analytics',
        'conditions': [
            {
                'rule': 'system_load > 0.8',
                'action': 'reduce_data_resolution'
            },
            {
                'rule': 'concurrent_users > 100',
                'action': 'enable_data_sampling'
            },
            {
                'rule': 'data_volume_mb > 100',
                'action': 'compress_response'
            }
        ],
        'default_behavior': 'full_resolution'
    })

    # Comprehensive audit logging
    analytics_logger = EventLogger({
        'name': 'analytics_audit',
        'log_events': ['query_start', 'query_end', 'cache_hit', 'cache_miss'],
        'include_metrics': True
    })

    return [metrics_state, perf_monitor, dashboard_cache, adaptive_processor, analytics_logger]

# Real-time analytics dashboard
analytics_system = create_analytics_dashboard()

def process_dashboard_request(dashboard_request):
    """Process dashboard requests with real-time analytics."""

    start_time = time.time()

    # Step 1: Update metrics state
    current_metrics = analytics_system[0].process({
        'state_key': 'global_metrics',
        'updates': {
            'total_requests': 'increment',
            'active_users': dashboard_request.get('user_count', 1)
        }
    })

    # Step 2: Check cache for dashboard data
    cache_key = {
        'dashboard_id': dashboard_request.get('dashboard_id'),
        'time_range': dashboard_request.get('time_range'),
        'filters': dashboard_request.get('filters', {})
    }

    cache_lookup = analytics_system[2].process({
        'cache_operation': 'get',
        **cache_key
    })

    if cache_lookup.get('cache_hit'):
        result = {
            'status': 'success',
            'data': cache_lookup['cached_data'],
            'source': 'cache',
            'cache_age': cache_lookup['cache']['age_seconds']
        }
    else:
        # Step 3: Apply adaptive processing based on load
        adaptive_request = analytics_system[3].process(dashboard_request)

        # Step 4: Generate analytics data
        analytics_data = generate_analytics_data(adaptive_request)

        # Step 5: Cache the result
        analytics_system[2].process({
            'cache_operation': 'set',
            'cache_data': analytics_data,
            'cache_ttl': 30,
            **cache_key
        })

        result = {
            'status': 'success',
            'data': analytics_data,
            'source': 'generated'
        }

    # Step 6: Performance monitoring
    processing_time = (time.time() - start_time) * 1000
    analytics_system[1].record_metric('response_time_ms', processing_time)

    # Step 7: Audit logging
    analytics_system[4].process({
        'event': 'dashboard_request',
        'user_id': dashboard_request.get('user_id'),
        'dashboard_id': dashboard_request.get('dashboard_id'),
        'processing_time_ms': processing_time,
        'cache_hit': result.get('source') == 'cache'
    })

    return result

def generate_analytics_data(request):
    """Generate analytics data based on request parameters."""
    # In a real implementation, this would query databases, perform calculations, etc.
    return {
        'timestamp': time.time(),
        'metrics': {
            'total_users': 1250,
            'active_sessions': 340,
            'error_rate': 0.02,
            'response_time_avg': 245
        },
        'charts': {
            'user_growth': [1000, 1100, 1150, 1200, 1250],
            'performance_trend': [300, 280, 250, 240, 245]
        },
        'alerts': []
    }
```

### Edge Computing Resource Management

```python
from eventflow_modules.functions import (
    ConditionalProcessor, RateLimiter, CacheManager,
    StateManager, CircuitBreaker
)

def create_edge_computing_pipeline():
    """Create resource-constrained edge computing pipeline."""

    # Adaptive processing based on battery/resource levels
    resource_adaptive = ConditionalProcessor({
        'name': 'resource_adaptive',
        'conditions': [
            {
                'rule': 'battery_level < 0.2',
                'action': 'minimum_processing_mode'
            },
            {
                'rule': 'memory_usage > 0.8',
                'action': 'reduce_batch_size'
            },
            {
                'rule': 'network_quality == "poor"',
                'action': 'compress_and_batch'
            }
        ],
        'default_behavior': 'normal_processing'
    })

    # Rate limiting for resource conservation
    resource_limiter = RateLimiter({
        'name': 'resource_limiter',
        'capacity': 50,  # Lower capacity for edge devices
        'refill_rate_per_second': 5,
        'algorithm': 'token_bucket'
    })

    # Aggressive caching for edge scenarios
    edge_cache = CacheManager({
        'name': 'edge_cache',
        'max_cache_size': 100,  # Limited memory
        'default_ttl_seconds': 600,  # Longer TTL for edge
        'eviction_policy': 'lru'
    })

    # State management for offline operation
    offline_state = StateManager({
        'name': 'offline_state',
        'state_key': 'edge_state'
    })

    # Circuit breaker for network-dependent operations
    network_circuit_breaker = CircuitBreaker({
        'name': 'network_circuit_breaker',
        'failure_threshold': 3,
        'recovery_timeout': 30.0,  # Faster recovery for edge
        'success_threshold': 2
    })

    return [resource_adaptive, resource_limiter, edge_cache, offline_state, network_circuit_breaker]

# Edge computing with resource constraints
edge_system = create_edge_computing_pipeline()

def process_edge_data(sensor_data):
    """Process data on resource-constrained edge devices."""

    # Step 1: Resource-aware processing
    resource_aware_data = edge_system[0].process({
        **sensor_data,
        'battery_level': get_battery_level(),
        'memory_usage': get_memory_usage(),
        'network_quality': assess_network_quality()
    })

    # Step 2: Rate limiting to conserve resources
    rate_check = edge_system[1].process(resource_aware_data)
    if not rate_check.get('rate_limit', {}).get('allowed', True):
        # Queue for later processing when resources available
        queue_for_later_processing(rate_check)
        return {'status': 'queued_resource_limit'}

    # Step 3: Check edge cache
    cache_lookup = edge_system[2].process({
        'cache_operation': 'get',
        'sensor_type': sensor_data.get('sensor_type'),
        'data_hash': hash(str(sensor_data.get('data', {})))
    })

    if cache_lookup.get('cache_hit'):
        return {
            'status': 'cache_hit',
            'data': cache_lookup['cached_data'],
            'processing_mode': 'cached'
        }

    # Step 4: Update offline state
    state_update = edge_system[3].process({
        'state_key': 'sensor_state',
        'updates': {
            'last_reading': time.time(),
            'data_points_collected': 'increment',
            'battery_used': 0.001  # Estimate battery usage
        }
    })

    # Step 5: Network-dependent processing with circuit breaker
    network_result = edge_system[4].process(state_update)

    if network_result.get('circuit_breaker', {}).get('state') == 'open':
        # Store locally when network is down
        store_locally(network_result)
        return {'status': 'stored_offline'}

    # Step 6: Process and cache result
    processed_data = perform_edge_processing(network_result)

    # Cache for future use
    edge_system[2].process({
        'cache_operation': 'set',
        'cache_data': processed_data,
        'cache_ttl': 600,
        'sensor_type': sensor_data.get('sensor_type'),
        'data_hash': hash(str(sensor_data.get('data', {})))
    })

    return {
        'status': 'processed',
        'data': processed_data,
        'processing_mode': 'real_time'
    }
```

## Advanced Integration Patterns

### Microservices Architecture with EventFlow

```python
from eventflow_modules.functions import (
    EventRouter, EventMultiplexer, StateManager,
    RetryHandler, CircuitBreaker
)

def create_microservices_mesh():
    """Create event-driven microservices communication mesh."""

    # Service discovery and routing
    service_router = EventRouter({
        'name': 'service_discovery',
        'routing_rules': [
            {
                'condition': 'service_type == "auth"',
                'output_stream': 'auth_service'
            },
            {
                'condition': 'service_type == "user"',
                'output_stream': 'user_service'
            },
            {
                'condition': 'service_type == "analytics"',
                'output_stream': 'analytics_service'
            }
        ]
    })

    # Event aggregation from multiple services
    event_aggregator = EventMultiplexer({
        'name': 'service_responses',
        'input_streams': ['auth_responses', 'user_responses', 'analytics_responses'],
        'sync_mode': 'timestamp_merge',
        'merge_window_ms': 100.0
    })

    # Distributed state management
    distributed_state = StateManager({
        'name': 'distributed_cache',
        'state_key': 'service_state'
    })

    # Fault tolerance for service calls
    service_retry = RetryHandler({
        'name': 'service_retry',
        'max_retries': 3,
        'retry_condition': 'service_unavailable',
        'backoff_strategy': 'exponential'
    })

    service_circuit_breaker = CircuitBreaker({
        'name': 'service_circuit_breaker',
        'failure_threshold': 5,
        'recovery_timeout': 120.0
    })

    return [service_router, event_aggregator, distributed_state, service_retry, service_circuit_breaker]

# Microservices communication mesh
service_mesh = create_microservices_mesh()

def handle_service_request(service_request):
    """Handle inter-service communication with fault tolerance."""

    # Route to appropriate service
    routing_decision = service_mesh[0].process(service_request)

    # Apply fault tolerance
    retry_result = service_mesh[3].process(routing_decision)

    if retry_result.get('retry', {}).get('scheduled'):
        return schedule_service_retry(retry_result)

    # Check circuit breaker
    circuit_result = service_mesh[4].process(retry_result)

    if circuit_result.get('circuit_breaker', {}).get('state') == 'open':
        return fallback_service_response(service_request)

    # Update distributed state
    state_update = service_mesh[2].process({
        'state_key': f"service_{service_request.get('service_id')}",
        'updates': {
            'last_request': time.time(),
            'request_count': 'increment'
        }
    })

    # Route to actual service
    service_response = route_to_microservice(state_update)

    # Aggregate responses if needed
    if service_request.get('requires_aggregation'):
        aggregated = service_mesh[1].process(service_response)
        return aggregated

    return service_response
```

These advanced infrastructure modules provide enterprise-grade capabilities for building scalable, fault-tolerant, and high-performance neuromorphic applications across diverse deployment scenarios.