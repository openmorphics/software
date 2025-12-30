# Environmental Air Quality Monitoring Example

This example demonstrates air quality monitoring using EventFlow's neuromorphic environmental sensing capabilities.

## Overview

The air quality monitoring algorithm combines data from multiple environmental sensors to provide comprehensive air quality assessment including particulate matter, gases, and atmospheric conditions. It computes air quality indices and generates alerts for pollution levels.

## Files

- `demo.py` - Basic air quality monitoring demonstration
- `README.md` - This documentation

## Usage

```bash
# Run the air quality monitoring demo
python demo.py

# Or use EventFlow CLI with environmental sensors
ef run --config air_quality_config.json --output air_quality_output.jsonl
```

## Algorithm Details

The air quality monitoring algorithm:
1. Fuses data from multiple environmental sensors (gas, particulate, chemical)
2. Applies pollutant-specific thresholds and temporal averaging
3. Computes overall air quality index (AQI) from multiple pollutants
4. Generates alerts based on configurable thresholds
5. Provides real-time environmental monitoring with low power consumption

## Supported Pollutants

- PM2.5 (Particulate Matter ≤2.5µm)
- PM10 (Particulate Matter ≤10µm)
- NO2 (Nitrogen Dioxide)
- CO (Carbon Monoxide)
- O3 (Ozone)
- VOC (Volatile Organic Compounds)

## Configuration

The algorithm supports:
- Configurable pollutant thresholds (EPA/WHO standards)
- Adjustable monitoring time windows
- Multiple alert levels (good, moderate, unhealthy)
- Sensor calibration offsets
- Multi-sensor data fusion

## Applications

- Urban air quality monitoring stations
- Industrial emission monitoring
- Indoor air quality systems
- Environmental research and studies
- Smart city infrastructure
- Personal air quality monitors