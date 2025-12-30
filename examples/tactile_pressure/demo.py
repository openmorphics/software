#!/usr/bin/env python3
"""
Tactile Pressure Detection Demo

This script demonstrates tactile pressure detection using EventFlow's
neuromorphic processing capabilities. It simulates a tactile sensor array
and processes pressure events in real-time.
"""

import sys
import time
from typing import List

# Add the local packages to Python path
sys.path.insert(0, '../../eventflow-sal')
sys.path.insert(0, '../../eventflow-core')
sys.path.insert(0, '../../eventflow-modules')

try:
    from eventflow_modules.tactile import pressure_detection
    from eventflow_sal.drivers.tactile import TactileFileSource
    from eventflow_core.eir.runtime import run_event_mode
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure EventFlow packages are installed in development mode:")
    print("  pip install -e ./eventflow-core")
    print("  pip install -e ./eventflow-sal")
    print("  pip install -e ./eventflow-modules")
    sys.exit(1)

def simulate_tactile_sensor() -> TactileFileSource:
    """
    Create a simulated tactile sensor for demonstration.

    Returns:
        TactileFileSource: Simulated tactile sensor source
    """
    # In a real application, you would connect to actual hardware
    # For demo purposes, we'll use synthetic data
    return TactileFileSource("tactile_data.jsonl")

def main():
    """Run the tactile pressure detection demo."""
    print("=== EventFlow Tactile Pressure Detection Demo ===\n")

    # Create tactile sensor source
    print("Setting up tactile sensor...")
    tactile_source = simulate_tactile_sensor()

    # Create pressure detection graph
    print("Creating pressure detection graph...")
    pressure_graph = pressure_detection(
        source=tactile_source,
        threshold=0.3,  # Detect pressure above 30%
        window="50 ms",  # 50ms integration window
        spatial_resolution=16,  # 16x16 sensor array
    )

    print("Configuration:")
    print(f"  - Pressure threshold: 30%")
    print(f"  - Temporal window: 50ms")
    print(f"  - Spatial resolution: 16x16 sensors")
    print()

    # Simulate processing (in real application, this would process live sensor data)
    print("Starting pressure detection simulation...")
    print("Press Ctrl+C to stop\n")

    try:
        # In a real application, you would use run_event_mode() to process live data
        # For demo, we'll just show the graph structure
        print("Graph structure:")
        print(f"  - Nodes: {len(pressure_graph.nodes)}")
        print(f"  - Connections: {len(pressure_graph.connections)}")
        print()

        # Simulate some pressure detection events
        print("Simulating pressure detection events:")
        events_simulated = 0

        for packet in tactile_source.subscribe():
            events_simulated += 1
            x = packet.meta.get('x', 0)
            y = packet.meta.get('y', 0)
            pressure = packet.value

            if pressure > 0.3:  # Above threshold
                print(f"  Pressure detected at ({x},{y}): {pressure:.2f}")

            if events_simulated >= 10:  # Limit demo output
                break

        print("\nDemo completed successfully!")
        print("\nThis demonstrates:")
        print("- Event-based tactile pressure processing")
        print("- Real-time threshold detection")
        print("- Spatial pressure mapping")
        print("- Neuromorphic event-driven computation")

    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"Error during demo: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())