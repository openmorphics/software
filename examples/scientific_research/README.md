# Scientific Research Module Examples

This directory contains examples demonstrating EventFlow's scientific research capabilities for laboratory data analysis, signal processing, and experimental measurement systems using neuromorphic computing.

## Overview

The scientific research module provides comprehensive support for:

- **Signal Processing**: FFT analysis, digital filtering, correlation analysis
- **Data Analysis**: Curve fitting, statistical analysis, regression modeling
- **Measurement Systems**: High-speed data acquisition, precision timing
- **Research Instruments**: Spectrometer, oscilloscope, and sensor control

All examples use EventFlow's neuromorphic computing architecture for energy-efficient, real-time scientific computing.

## Examples

### signal_processing_demo.py

Demonstrates core signal processing capabilities:

```bash
python signal_processing_demo.py
```

Features demonstrated:
- FFT analysis with configurable sampling rates and window sizes
- Digital signal filtering (lowpass, highpass, bandpass)
- Cross-correlation and auto-correlation analysis
- Real-time processing with synthetic sensor data

### spectrometer_demo.py (Future)

Will demonstrate spectrometer control and spectral analysis for:
- UV-Vis spectroscopy
- Raman spectroscopy
- Spectral data processing and analysis

### oscilloscope_demo.py (Future)

Will demonstrate oscilloscope control for:
- Multi-channel data acquisition
- Trigger configuration
- Waveform analysis

## Data Sources

Examples use synthetic data sources that simulate real laboratory instruments:

- `lab.spectrometer://file?spectrum.csv` - Spectral data files
- `lab.oscilloscope://file?scope.csv` - Oscilloscope waveforms
- `lab.sensor://file?sensor.csv` - Scientific sensor readings

## Running Examples

All examples can be run from the repository root:

```bash
# Signal processing demo
python examples/scientific_research/signal_processing_demo.py

# Using EventFlow CLI
ef run --config scientific_config.json --output results.jsonl
```

## Configuration

Examples support configuration through JSON files:

```json
{
  "nodes": [
    {
      "id": "fft_processor",
      "op": "fft_analysis",
      "params": {
        "sampling_rate": 1000.0,
        "window_size": 1024,
        "overlap": 0.5
      }
    }
  ]
}
```

## Applications

These examples demonstrate applications in:

- **Physics Research**: Signal analysis, spectroscopy, particle detection
- **Chemistry**: Analytical instrument control, reaction monitoring
- **Biology**: Biosensor data processing, physiological signal analysis
- **Engineering**: Vibration analysis, control systems, quality control
- **Environmental Science**: Sensor network data processing

## Performance

Examples showcase EventFlow's neuromorphic advantages:
- Low-power real-time processing
- Event-driven computation efficiency
- Deterministic execution across backends
- Scalable to high-speed data streams

## Integration

Scientific research module integrates with:
- SAL for laboratory instrument connectivity
- EventFlow CLI for batch processing
- EIR graphs for custom processing pipelines
- Cross-backend compatibility (Python/Rust)</content>
</xai:function_call">{"path":"examples/scientific_research/README.md","operation":"created","notice":"You do not need to re-read the file, as you have seen all changes Proceed with the task using these changes as the new baseline."}...