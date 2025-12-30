# Industrial Quality Control Example

This example demonstrates quality control monitoring for manufacturing processes using neuromorphic processing for real-time defect detection and parameter control.

## Overview

The quality control module monitors manufacturing processes to:

- Detect defects and quality issues in real-time
- Monitor process parameters against control limits
- Provide statistical process control (SPC)
- Support different manufacturing process types

## Usage

```bash
cd examples/industrial_quality_control
python demo.py
```

## Algorithm Details

The quality control uses:

- **Process-Specific Monitoring**: Configurable parameters for different manufacturing processes
- **Defect Detection**: Event-based thresholding for quality issues
- **Parameter Control**: Statistical control limits monitoring
- **Quality Assessment**: Temporal integration for overall process quality

## Supported Process Types

- **Assembly**: Position, force, torque monitoring
- **Machining**: Speed, feed, depth monitoring
- **Welding**: Current, voltage, temperature monitoring
- **Packaging**: Weight, dimension, pressure monitoring
- **Casting**: Temperature, flow, pressure monitoring
- **Generic**: Custom parameter configuration

## Control Limits

The example demonstrates statistical process control with:

- **Upper Control Limits (UCL)**: Maximum acceptable values
- **Lower Control Limits (LCL)**: Minimum acceptable values
- **Parameter Tolerance**: Acceptable deviation ranges

## Configuration Parameters

- `process_type`: Type of manufacturing process
- `defect_threshold`: Threshold for defect detection (0.0-1.0)
- `parameter_tolerance`: Tolerance for parameter control (0.0-1.0)
- `monitoring_window`: Time window for quality assessment
- `control_limits`: Statistical control limits dictionary

## Output Analysis

The demo provides:
- Quality assessment event counts
- Defect detection alerts
- Control limit violation reports
- Parameter deviation monitoring
- Overall process quality status

## Applications

- Manufacturing process monitoring
- Quality assurance systems
- Statistical process control
- Real-time defect detection
- Process optimization
- Industrial automation