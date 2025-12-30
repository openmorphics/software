#!/usr/bin/env python3
"""
EventFlow Industrial Vibration Analysis Demo

This example demonstrates vibration analysis for bearing fault detection
using neuromorphic processing. It shows how to use FFT analysis and spectral
monitoring to detect characteristic bearing frequencies.
"""

import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

try:
    from eventflow_sal.drivers.industrial import VibrationFileSource
    from eventflow_core.eir.runtime import run_event_mode
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure EventFlow is properly installed or run from the repository root.")
    sys.exit(1)

try:
    from eventflow_modules.industrial import vibration_analysis
except ImportError as e:
    print(f"Industrial module import error: {e}")
    print("The industrial module may not be properly installed.")
    sys.exit(1)

def main():
    print("EventFlow Industrial Vibration Analysis Demo")
    print("=" * 50)

    # Create vibration sensor source
    vibration_source = VibrationFileSource("vibration_data.sim")

    # Configure vibration analysis with bearing fault detection
    bearing_freqs = {
        "BPFO": 120.5,  # Ball Pass Frequency Outer
        "BPFI": 180.3,  # Ball Pass Frequency Inner
        "BSF": 65.2     # Ball Spin Frequency
    }

    # Create vibration analysis graph
    vib_graph = vibration_analysis(
        source=vibration_source,
        sampling_rate=1000.0,
        fft_size=1024,
        threshold=0.2,
        bearing_freqs=bearing_freqs
    )

    print(f"Created vibration analysis graph with {len(vib_graph.nodes)} nodes")
    print(f"Bearing frequencies monitored: {list(bearing_freqs.keys())}")

    # Run the vibration analysis
    print("\nRunning vibration analysis...")
    try:
        # Run for a short simulation period
        results = run_event_mode(vib_graph, max_steps=1000)

        print("Analysis complete!")
        print(f"Processed {len(results.get('vibration', []))} vibration events")
        print(f"Detected {len(results.get('fft', []))} FFT bins")

        # Check for anomalies
        anomaly_count = len(results.get('vibration', []))
        if anomaly_count > 0:
            print(f"⚠️  Detected {anomaly_count} vibration anomalies")

        # Check spectral analysis results
        for freq_name in bearing_freqs.keys():
            spectral_events = results.get(f'spectral_{freq_name}', [])
            if spectral_events:
                print(f"📊 {freq_name} frequency detected {len(spectral_events)} times")

    except Exception as e:
        print(f"Error running vibration analysis: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())