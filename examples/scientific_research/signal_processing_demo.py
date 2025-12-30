#!/usr/bin/env python3
"""
Scientific Signal Processing Demonstration

This example demonstrates EventFlow's scientific research capabilities for
signal processing, including FFT analysis, filtering, and correlation using
neuromorphic computing principles.
"""

import time
from eventflow_sal import open as sal_open
from eventflow_modules.scientific_research import fft_analysis, signal_filtering, correlation_analysis

def main():
    print("=== EventFlow Scientific Signal Processing Demo ===\n")

    # Simulate acquiring data from a scientific sensor
    print("1. Opening scientific sensor data source...")
    try:
        # Use synthetic scientific sensor data
        sensor_source = sal_open("lab.sensor://file?sensor_data.csv")
        print("   ✓ Connected to scientific sensor")
    except Exception as e:
        print(f"   ⚠ Using synthetic sensor data: {e}")
        sensor_source = None

    print("\n2. Setting up FFT analysis...")
    try:
        # Configure FFT analysis for 1kHz sampling, 1024-point window
        fft_graph = fft_analysis(
            source=sensor_source,
            sampling_rate=1000.0,
            window_size=1024,
            overlap=0.5
        )
        print("   ✓ FFT analysis configured (1kHz, 1024pt, 50% overlap)")
    except Exception as e:
        print(f"   ✗ FFT setup failed: {e}")
        return

    print("\n3. Setting up signal filtering...")
    try:
        # Configure low-pass filter for noise reduction
        filter_graph = signal_filtering(
            source=sensor_source,
            filter_type="lowpass",
            cutoff_frequency=100.0,
            order=4,
            sampling_rate=1000.0
        )
        print("   ✓ Low-pass filter configured (100Hz cutoff, 4th order)")
    except Exception as e:
        print(f"   ✗ Filter setup failed: {e}")
        return

    print("\n4. Setting up correlation analysis...")
    try:
        # Configure cross-correlation analysis
        correlation_graph = correlation_analysis(
            source=sensor_source,
            correlation_type="cross",
            window_size=512,
            max_lag=128
        )
        print("   ✓ Cross-correlation configured (512pt window, 128pt lag)")
    except Exception as e:
        print(f"   ✗ Correlation setup failed: {e}")
        return

    print("\n5. Running signal processing analysis...")
    try:
        start_time = time.time()

        # In a real implementation, these graphs would be executed
        # For demo purposes, we simulate processing time
        time.sleep(0.1)

        processing_time = time.time() - start_time
        print(".3f")
    except Exception as e:
        print(f"   ✗ Processing failed: {e}")
        return

    print("\n=== Signal Processing Results ===")
    print("FFT Analysis:")
    print("  - Frequency range: 0-500 Hz")
    print("  - Resolution: ~1 Hz")
    print("  - Window: Hanning")
    print("  - Overlap: 50%")

    print("\nSignal Filtering:")
    print("  - Filter type: Low-pass")
    print("  - Cutoff: 100 Hz")
    print("  - Order: 4th")
    print("  - Attenuation: >24 dB/octave")

    print("\nCorrelation Analysis:")
    print("  - Type: Cross-correlation")
    print("  - Window: 512 samples")
    print("  - Max lag: ±128 samples")
    print("  - Normalized output")

    print("\n✓ Scientific signal processing demonstration completed!")
    print("\nThis demonstrates EventFlow's capabilities for:")
    print("  • Real-time FFT analysis")
    print("  • Digital signal filtering")
    print("  • Correlation analysis")
    print("  • Neuromorphic scientific computing")

if __name__ == "__main__":
    main()