# Industrial Predictive Maintenance Example

This example demonstrates predictive maintenance using anomaly detection and equipment health monitoring with neuromorphic processing.

## Overview

The predictive maintenance module analyzes sensor data from industrial equipment to:

- Detect anomalies in equipment operation
- Predict potential failures before they occur
- Monitor equipment health over time
- Support different types of industrial equipment

## Usage

```bash
cd examples/industrial_predictive_maintenance
python demo.py
```

## Algorithm Details

The predictive maintenance uses:

- **Equipment-Specific Monitoring**: Configurable sensor patterns for different equipment types
- **Anomaly Detection**: LIF neurons for adaptive threshold detection
- **Health Assessment**: Temporal integration for overall equipment health scoring
- **Failure Prediction**: Combined anomaly analysis for failure forecasting

## Supported Equipment Types

- **Motor**: Vibration, current, temperature monitoring
- **Pump**: Pressure, flow, vibration monitoring
- **Bearing**: Vibration, temperature, speed monitoring
- **Conveyor**: Speed, load, vibration monitoring
- **Compressor**: Pressure, temperature, current monitoring
- **Generic**: Custom sensor configuration

## Configuration Parameters

- `equipment_type`: Type of equipment being monitored
- `failure_threshold`: Health score threshold for failure prediction (0.0-1.0)
- `health_window`: Time window for health assessment
- `anomaly_sensitivity`: Sensitivity for anomaly detection (0.0-1.0)

## Output Analysis

The demo provides:
- Health assessment event counts
- Failure prediction alerts
- Anomaly detection by parameter type
- Overall equipment health status

## Applications

- Rotating equipment monitoring
- Process equipment predictive maintenance
- Asset health management
- Condition-based maintenance systems
- Industrial IoT predictive analytics