# Industrial Vibration Analysis Example

This example demonstrates vibration analysis for predictive maintenance and bearing fault detection using EventFlow's neuromorphic processing capabilities.

## Overview

The vibration analysis module processes accelerometer data from industrial equipment to:

- Perform FFT-based frequency domain analysis
- Detect bearing characteristic frequencies (BPFO, BPFI, BSF)
- Identify vibration anomalies in real-time
- Support various sampling rates and FFT sizes

## Usage

```bash
cd examples/industrial_vibration
python demo.py
```

## Algorithm Details

The vibration analysis uses:

- **FFT Processing**: BucketSum operation simulates FFT binning for frequency analysis
- **Spectral Monitoring**: Dedicated nodes for each bearing characteristic frequency
- **Anomaly Detection**: EventFuse operations for threshold-based vibration monitoring
- **Real-time Processing**: Neuromorphic operations for low-latency industrial monitoring

## Configuration

Key parameters:
- `sampling_rate`: Sensor sampling frequency (Hz)
- `fft_size`: FFT window size (must be power of 2)
- `threshold`: Vibration anomaly detection threshold
- `bearing_freqs`: Dictionary of characteristic bearing frequencies

## Bearing Frequency Calculations

The example includes typical bearing characteristic frequencies:
- **BPFO** (Ball Pass Frequency Outer): Frequency at which balls pass outer race
- **BPFI** (Ball Pass Frequency Inner): Frequency at which balls pass inner race
- **BSF** (Ball Spin Frequency): Frequency at which balls spin on themselves

## Output

The demo outputs:
- Number of vibration events processed
- FFT analysis results
- Detected anomalies
- Spectral analysis for each bearing frequency

## Applications

- Bearing fault detection
- Gearbox monitoring
- Motor vibration analysis
- Structural health monitoring
- Predictive maintenance systems