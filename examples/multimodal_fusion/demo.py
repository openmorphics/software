#!/usr/bin/env python3
"""
Multi-Modal Sensor Fusion Demo

This script demonstrates multi-modal sensor fusion using EventFlow's
neuromorphic processing capabilities. It shows how to combine vision,
audio, IMU, and other sensor streams for enhanced scene understanding
and contextual awareness.
"""

import sys
import time
from typing import List

# Add the local packages to Python path
sys.path.insert(0, '../../eventflow-sal')
sys.path.insert(0, '../../eventflow-core')
sys.path.insert(0, '../../eventflow-modules')

try:
    from eventflow_modules.multimodal_fusion import (
        kalman_filter, data_association, temporal_alignment,
        scene_understanding, feature_extraction, decision_fusion
    )
    from eventflow_sal.drivers.fusion import FusionSource
    from eventflow_core.eir.runtime import run_event_mode
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure EventFlow packages are installed in development mode:")
    print("  pip install -e ./eventflow-core")
    print("  pip install -e ./eventflow-sal")
    print("  pip install -e ./eventflow-modules")
    sys.exit(1)

def simulate_multimodal_sensors() -> List[any]:
    """
    Create simulated multi-modal sensor sources for demonstration.

    Returns:
        List: Simulated sensor sources (vision, audio, IMU, etc.)
    """
    # In a real application, you would connect to actual hardware sensors
    # For demo purposes, we'll use synthetic fusion data
    return [
        FusionSource(sources=["vision", "audio"], fusion_type="kalman"),
        FusionSource(sources=["imu", "environmental"], fusion_type="probabilistic"),
    ]

def main():
    """Run the multi-modal sensor fusion demo."""
    print("=== EventFlow Multi-Modal Sensor Fusion Demo ===\n")

    # Create multi-modal sensor sources
    print("Setting up multi-modal sensor sources...")
    sensor_sources = simulate_multimodal_sensors()

    # Create Kalman filter for sensor fusion
    print("Creating Kalman filter for sensor fusion...")
    fusion_graph = kalman_filter(
        sources=sensor_sources,
        state_dim=6,  # position (x,y,z) + velocity (vx,vy,vz)
        measurement_dim=4,  # vision + audio + IMU + environmental
        process_noise=0.1,
        measurement_noise=0.5,
        window="100 ms"
    )

    # Create data association for multi-modal tracking
    print("Creating data association for object tracking...")
    association_graph = data_association(
        sources=sensor_sources,
        max_distance=1.5,
        algorithm="nearest_neighbor",
        window="50 ms"
    )

    # Create temporal alignment for synchronized processing
    print("Creating temporal alignment for sensor synchronization...")
    alignment_graph = temporal_alignment(
        sources=sensor_sources,
        sync_method="timestamp",
        max_delay="200 ms",
        interpolation="linear"
    )

    # Create scene understanding for contextual awareness
    print("Creating scene understanding for contextual processing...")
    scene_graph = scene_understanding(
        sources=sensor_sources,
        context_model="hierarchical",
        confidence_threshold=0.8,
        max_objects=25
    )

    # Create feature extraction for multi-modal representations
    print("Creating feature extraction for unified representations...")
    feature_graph = feature_extraction(
        sources=sensor_sources,
        feature_types=["spatial", "temporal", "spectral"],
        dimensionality=256,
        fusion_method="attention"
    )

    # Create decision fusion for robust classification
    print("Creating decision fusion for multi-modal decisions...")
    decision_graph = decision_fusion(
        sources=sensor_sources,
        fusion_type="probabilistic",
        voting_method="weighted",
        confidence_weighting=True
    )

    print("\nFusion Configuration:")
    print("  - Kalman Filter: 6D state, 4D measurements")
    print("  - Data Association: Nearest neighbor, max distance 1.5")
    print("  - Temporal Alignment: Timestamp-based, 200ms max delay")
    print("  - Scene Understanding: Hierarchical model, 25 max objects")
    print("  - Feature Extraction: 256D attention-based fusion")
    print("  - Decision Fusion: Probabilistic with confidence weighting")
    print()

    # Simulate processing (in real application, this would process live sensor data)
    print("Starting multi-modal fusion simulation...")
    print("Press Ctrl+C to stop\n")

    try:
        # Demonstrate fusion source data generation
        print("Fusion data stream simulation:")
        fusion_source = FusionSource(sources=["vision", "audio", "imu"], fusion_type="kalman")
        events_simulated = 0

        for packet in fusion_source.subscribe():
            events_simulated += 1
            fusion_data = packet.meta.get('fusion_data', {})

            print(f"  Fusion event {events_simulated}:")
            print(f"    Vision features: {len(fusion_data.get('vision_features', []))} dims")
            print(f"    Audio features: {len(fusion_data.get('audio_features', []))} dims")
            print(f"    IMU features: {len(fusion_data.get('imu_features', []))} dims")
            print(f"    Confidence: {fusion_data.get('confidence', 0):.2f}")
            print(f"    Timestamp: {packet.t_ns} ns")
            print()

            if events_simulated >= 5:  # Limit demo output
                break

        print("\nDemo completed successfully!")
        print("\nThis demonstrates:")
        print("- Multi-modal sensor fusion with Kalman filtering")
        print("- Data association across sensor modalities")
        print("- Temporal synchronization of sensor streams")
        print("- Scene understanding with contextual awareness")
        print("- Feature extraction from heterogeneous sensors")
        print("- Decision fusion for robust classification")
        print("- Real-time neuromorphic event processing")

    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"Error during demo: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())