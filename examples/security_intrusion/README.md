# Security Intrusion Detection Example

This example demonstrates EventFlow's security/surveillance capabilities for intrusion detection, threat assessment, and automated security responses using neuromorphic computing.

## Overview

The security/surveillance module implements energy-efficient security monitoring algorithms that process sensor data from motion detectors, cameras, and perimeter sensors to detect intrusions and assess threats in real-time.

## Features Demonstrated

- **Intrusion Detection**: Motion tracking and anomaly detection using spatial-temporal event processing
- **Threat Assessment**: Behavior analysis and risk evaluation using spiking neural networks
- **Security Automation**: Alert generation and response coordination with multi-channel processing
- **Sensor Fusion**: Integration of multiple security sensor types with camera networks
- **Energy Efficiency**: Neuromorphic algorithms optimized for low-power security systems

## Algorithm Components

### 1. Intrusion Detection (`intrusion_detection`)
- Motion pattern analysis with configurable thresholds
- Spatial perimeter monitoring with zone-specific detection
- Anomaly detection using event correlation
- Real-time motion tracking with temporal history

### 2. Threat Assessment (`threat_assessment`)
- Spiking neural network-based behavior analysis
- Multi-channel parallel threat classification
- Risk evaluation with configurable thresholds
- Temporal pattern recognition for sustained threats

### 3. Security Automation (`security_automation`)
- Automated alert generation based on threat levels
- Multi-channel response coordination
- Escalation management with timed responses
- Feedback loops for sustained monitoring

## Running the Example

```bash
cd examples/security_intrusion
python demo.py
```

## Configuration

The demo uses synthetic security sensor data to simulate:
- Motion detector events with varying intensity levels
- Camera motion detection coordinates
- Perimeter sensor breach events

### Key Parameters

- **Motion Threshold**: 50% (configurable 0.0-1.0)
- **Anomaly Window**: 1 second temporal analysis
- **Spatial Resolution**: 64x64 perimeter grid
- **Risk Threshold**: 70% for threat classification
- **Alert Threshold**: 80% for automated responses

## Sensor Integration

The example integrates multiple security sensor types:

### Motion Detectors (`security.motion_detector://`)
- PIR sensor simulation with zone-based detection
- Configurable sensitivity thresholds
- Temporal event correlation

### Security Cameras (`security.camera://`)
- Motion detection with spatial coordinates
- Frame-based processing simulation
- Coverage area mapping

### Perimeter Sensors (`security.perimeter_sensor://`)
- Fence/infrared beam breach detection
- Multiple zone monitoring
- Breach type classification (intrusion/disturbance)

## Performance Characteristics

- **Energy Efficient**: Event-driven processing minimizes power consumption
- **Real-time**: Sub-millisecond response times for critical alerts
- **Scalable**: Supports multiple camera networks and sensor arrays
- **Deterministic**: Consistent behavior across different backend implementations

## Applications

- **Facility Security**: Building perimeter monitoring and access control
- **Smart Cities**: Public space surveillance with automated responses
- **Industrial Security**: Critical infrastructure protection
- **Residential Security**: Home automation with intelligent threat detection

## Integration with EventFlow

The security module follows EventFlow patterns:
- EIR graph-based processing pipelines
- SAL integration for sensor abstraction
- Cross-backend compatibility (CPU, GPU, neuromorphic hardware)
- Deterministic execution with proper error handling

## Extending the Example

To integrate with real security hardware:
1. Replace synthetic sensor sources with actual device drivers
2. Configure sensor URIs (e.g., `security.camera://camera1`)
3. Adjust thresholds based on environmental conditions
4. Add custom threat patterns and response actions

## Security Considerations

- **Privacy**: Event-based processing minimizes data storage
- **Reliability**: Redundant sensor coverage and failover mechanisms
- **False Positives**: Configurable thresholds and temporal filtering
- **Response Safety**: Coordinated multi-channel verification before actions