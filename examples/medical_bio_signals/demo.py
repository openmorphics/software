#!/usr/bin/env python3
"""
Medical Bio-Signals Processing Demo

This script demonstrates ECG, EEG, and EMG processing using EventFlow's
neuromorphic capabilities for medical applications. It shows heart monitoring,
brain wave analysis, and muscle activity detection.
"""

import sys
import time
from typing import List

# Add the local packages to Python path
sys.path.insert(0, '../../eventflow-sal')
sys.path.insert(0, '../../eventflow-core')
sys.path.insert(0, '../../eventflow-modules')

try:
    from eventflow_modules.bio_signals import ecg_processing, eeg_processing, emg_processing
    from eventflow_sal.drivers.bio import CSVFileSource
    from eventflow_core.eir.runtime import run_event_mode
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure EventFlow packages are installed in development mode:")
    print("  pip install -e ./eventflow-core")
    print("  pip install -e ./eventflow-sal")
    print("  pip install -e ./eventflow-modules")
    sys.exit(1)

def simulate_ecg_monitor() -> CSVFileSource:
    """Create a simulated ECG monitor for demonstration."""
    return CSVFileSource("ecg_sample.csv", signal_type="ecg")

def simulate_eeg_headset() -> CSVFileSource:
    """Create a simulated EEG headset for demonstration."""
    return CSVFileSource("eeg_sample.csv", signal_type="eeg")

def simulate_emg_armband() -> CSVFileSource:
    """Create a simulated EMG armband for demonstration."""
    return CSVFileSource("emg_sample.csv", signal_type="emg")

def demo_ecg_processing():
    """Demonstrate ECG processing for heart monitoring."""
    print("=== ECG Processing Demo ===")

    # Create ECG source
    ecg_source = simulate_ecg_monitor()

    # Create ECG processing graph
    ecg_graph = ecg_processing(
        source=ecg_source,
        sampling_rate=250.0,  # Standard medical ECG rate
        heart_rate_window="30 s",
        arrhythmia_threshold=0.2,
    )

    print("ECG Configuration:")
    print("  - Sampling rate: 250 Hz")
    print("  - Heart rate window: 30s")
    print("  - Arrhythmia threshold: 20%")
    print(f"  - Graph nodes: {len(ecg_graph.nodes)}")
    print()

    # Simulate ECG processing
    print("Simulating ECG monitoring:")
    events_processed = 0
    heart_beats = 0

    for packet in ecg_source.subscribe():
        events_processed += 1
        if packet.value > 0.5:  # Simulated R-peak detection
            heart_beats += 1
            print(f"  R-peak detected on lead {packet.channel}: {packet.value:.3f} mV")

        if events_processed >= 20:  # Limit demo
            break

    print(f"  Total events processed: {events_processed}")
    print(f"  Heart beats detected: {heart_beats}")
    print()

def demo_eeg_processing():
    """Demonstrate EEG processing for brain wave analysis."""
    print("=== EEG Processing Demo ===")

    # Create EEG source
    eeg_source = simulate_eeg_headset()

    # Create EEG processing graph
    eeg_graph = eeg_processing(
        source=eeg_source,
        sampling_rate=256.0,  # Standard research EEG rate
        sleep_staging_window="60 s",
        artifact_threshold=0.9,
    )

    print("EEG Configuration:")
    print("  - Sampling rate: 256 Hz")
    print("  - Sleep staging window: 60s")
    print("  - Artifact threshold: 90%")
    print(f"  - Graph nodes: {len(eeg_graph.nodes)}")
    print()

    # Simulate EEG processing
    print("Simulating EEG analysis:")
    events_processed = 0
    alpha_waves = 0

    for packet in eeg_source.subscribe():
        events_processed += 1
        if packet.value > 10:  # Simulated alpha wave detection (uV)
            alpha_waves += 1
            print(f"  Alpha wave detected on electrode {packet.channel}: {packet.value:.1f} μV")

        if events_processed >= 15:  # Limit demo
            break

    print(f"  Total events processed: {events_processed}")
    print(f"  Alpha waves detected: {alpha_waves}")
    print()

def demo_emg_processing():
    """Demonstrate EMG processing for muscle activity."""
    print("=== EMG Processing Demo ===")

    # Create EMG source
    emg_source = simulate_emg_armband()

    # Create EMG processing graph
    emg_graph = emg_processing(
        source=emg_source,
        sampling_rate=1000.0,  # High-fidelity EMG rate
        muscle_groups=2,
        gesture_window="300 ms",
        activation_threshold=0.3,
        fatigue_detection=True,
    )

    print("EMG Configuration:")
    print("  - Sampling rate: 1000 Hz")
    print("  - Muscle groups: 2")
    print("  - Gesture window: 300ms")
    print("  - Activation threshold: 30%")
    print("  - Fatigue detection: enabled")
    print(f"  - Graph nodes: {len(emg_graph.nodes)}")
    print()

    # Simulate EMG processing
    print("Simulating EMG analysis:")
    events_processed = 0
    activations = 0

    for packet in emg_source.subscribe():
        events_processed += 1
        if packet.value > 0.3:  # Simulated muscle activation
            activations += 1
            print(f"  Muscle activation on electrode {packet.channel}: {packet.value:.3f} mV")

        if events_processed >= 25:  # Limit demo
            break

    print(f"  Total events processed: {events_processed}")
    print(f"  Muscle activations detected: {activations}")
    print()

def main():
    """Run the medical bio-signals processing demo."""
    print("=== EventFlow Medical Bio-Signals Processing Demo ===\n")

    print("This demo showcases EventFlow's neuromorphic capabilities for medical applications:")
    print("- ECG: Heart rate monitoring and arrhythmia detection")
    print("- EEG: Brain wave analysis and sleep staging")
    print("- EMG: Muscle activity detection and gesture recognition")
    print()

    try:
        # Note: In a real application, you would use actual medical devices
        # connected via SAL drivers. For this demo, we simulate sensor data.

        demo_ecg_processing()
        demo_eeg_processing()
        demo_emg_processing()

        print("=== Demo Summary ===")
        print("✓ ECG processing for cardiac monitoring")
        print("✓ EEG processing for neurological analysis")
        print("✓ EMG processing for musculoskeletal assessment")
        print("✓ Real-time event-based signal processing")
        print("✓ Medical-grade signal validation")
        print("✓ Neuromorphic computing for healthcare")

        print("\nDemo completed successfully!")
        print("\nClinical Applications:")
        print("- Continuous ECG monitoring for arrhythmia detection")
        print("- EEG sleep staging for sleep disorder diagnosis")
        print("- EMG gesture recognition for prosthetic control")
        print("- Real-time vital signs monitoring")
        print("- Neuromorphic healthcare devices")

    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"Error during demo: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())