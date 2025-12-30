# Multi-Modal Sensor Fusion Example

This example demonstrates EventFlow's multi-modal sensor fusion capabilities for enhanced scene understanding and contextual awareness using neuromorphic computing.

## Overview

Multi-modal sensor fusion combines data from multiple sensor types (vision, audio, IMU, tactile, environmental) to create richer scene representations than single-modality processing. This example shows how to:

- Fuse sensor data using Kalman filtering
- Associate detections across modalities
- Synchronize temporal streams
- Extract contextual scene understanding
- Perform decision fusion for robust classification

## Key Features Demonstrated

### Sensor Fusion Algorithms
- **Kalman Filtering**: Optimal state estimation from noisy multi-modal measurements
- **Data Association**: Linking detections across vision, audio, and IMU sensors
- **Temporal Alignment**: Synchronizing asynchronous sensor streams
- **Scene Understanding**: Hierarchical contextual processing
- **Feature Extraction**: Unified representations from heterogeneous sensors
- **Decision Fusion**: Consensus-based classification with confidence weighting

### Real-Time Processing
- Event-driven neuromorphic computation
- Deterministic execution across backends
- Low-latency multi-modal processing

## Usage

```bash
# Run the demonstration
python demo.py
```

## Sensor Modalities Supported

- **Vision**: Object detection, tracking, optical flow
- **Audio**: Sound localization, speech recognition, acoustic scene analysis
- **IMU**: Motion sensing, orientation, acceleration
- **Tactile**: Pressure detection, texture analysis
- **Bio-signals**: ECG, EEG, EMG processing
- **Environmental**: Air quality, gas detection, vibration analysis
- **Industrial**: Predictive maintenance, quality control

## Fusion Pipeline

```
Sensors → Temporal Alignment → Kalman Filter → Data Association → Feature Extraction → Scene Understanding → Decision Fusion
```

## Configuration Options

### Kalman Filter
- `state_dim`: State vector dimensions (position, velocity, etc.)
- `measurement_dim`: Measurement vector dimensions
- `process_noise`: Process uncertainty model
- `measurement_noise`: Sensor noise characteristics

### Data Association
- `max_distance`: Maximum association distance threshold
- `algorithm`: Association method (nearest_neighbor, hungarian, probabilistic)

### Temporal Alignment
- `sync_method`: Synchronization approach (timestamp, PLL, correlation)
- `max_delay`: Maximum temporal offset allowed
- `interpolation`: Missing data interpolation method

### Scene Understanding
- `context_model`: Contextual modeling (hierarchical, graph, attention)
- `confidence_threshold`: Minimum detection confidence
- `max_objects`: Maximum objects to track

## Applications

- **Autonomous Vehicles**: Sensor fusion for perception and navigation
- **Robotics**: Multi-modal scene understanding for manipulation
- **Smart Homes**: Contextual awareness from multiple sensors
- **Industrial IoT**: Predictive maintenance with sensor correlation
- **Healthcare**: Multi-modal patient monitoring and diagnostics
- **Security**: Enhanced surveillance with fused detection

## Performance Characteristics

- **Real-time**: Sub-millisecond fusion latency
- **Energy Efficient**: Event-driven processing minimizes computation
- **Robust**: Handles sensor failures and noise gracefully
- **Scalable**: Supports variable numbers of sensors and modalities

## Integration with EventFlow

This example integrates with EventFlow's:

- **EIR Graphs**: Declarative sensor processing pipelines
- **SAL Drivers**: Multi-modal sensor data acquisition
- **Runtime Engine**: Deterministic neuromorphic execution
- **Cross-Backend Compatibility**: Consistent behavior across platforms

## Extending the Example

To add new sensor modalities:

1. Create new SAL driver in `eventflow_sal/drivers/`
2. Add fusion algorithms in `eventflow_modules/multimodal_fusion/`
3. Update registry in `eventflow_sal/registry.py`
4. Extend the demo with new sensor integration

For custom fusion algorithms:

1. Implement new fusion function following EIR patterns
2. Add to `eventflow_modules/multimodal_fusion/__init__.py`
3. Update demo to showcase new capabilities