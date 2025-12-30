# Tactile Pressure Detection Example

This example demonstrates tactile pressure detection using EventFlow's neuromorphic processing capabilities.

## Overview

The tactile pressure detection algorithm processes pressure sensor events from tactile arrays to detect contact pressure above specified thresholds. It uses event-based processing to provide real-time pressure sensing with low latency and power consumption.

## Files

- `demo.py` - Basic tactile pressure detection demonstration
- `README.md` - This documentation

## Usage

```bash
# Run the tactile pressure detection demo
python demo.py

# Or use EventFlow CLI with tactile sensors
ef run --config tactile_config.json --output tactile_output.jsonl
```

## Algorithm Details

The pressure detection algorithm:
1. Maps tactile sensor coordinates to processing channels
2. Applies temporal thresholding for noise reduction
3. Detects pressure events above configurable thresholds
4. Provides spatial-temporal pressure information

## Configuration

The algorithm supports:
- Configurable pressure thresholds (0.0-1.0)
- Adjustable temporal windows for integration
- Variable spatial resolution (up to 256x256 sensors)
- Optional spatial smoothing for noise reduction

## Applications

- Robotic grasping and manipulation
- Prosthetic limb control
- Human-machine interfaces
- Quality control and inspection systems
- Medical pressure monitoring