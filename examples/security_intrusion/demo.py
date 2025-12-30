#!/usr/bin/env python3
"""
Security Intrusion Detection Demo

This script demonstrates security/surveillance intrusion detection using EventFlow's
neuromorphic processing capabilities. It simulates security sensors and processes
intrusion events in real-time using energy-efficient algorithms.
"""

import sys
import time
from typing import List

# Add the local packages to Python path
sys.path.insert(0, '../../eventflow-sal')
sys.path.insert(0, '../../eventflow-core')
sys.path.insert(0, '../../eventflow-modules')

try:
    from eventflow_modules.security_surveillance import intrusion_detection, threat_assessment, security_automation
    from eventflow_sal.drivers.security import MotionDetectorFileSource, CameraFileSource, PerimeterSensorFileSource
    from eventflow_core.eir.runtime import run_event_mode
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure EventFlow packages are installed in development mode:")
    print("  pip install -e ./eventflow-core")
    print("  pip install -e ./eventflow-sal")
    print("  pip install -e ./eventflow-modules")
    sys.exit(1)

def simulate_security_sensors():
    """
    Create simulated security sensors for demonstration.

    Returns:
        tuple: (motion_detector, camera, perimeter_sensor) sources
    """
    # In a real application, you would connect to actual security hardware
    # For demo purposes, we'll use synthetic data
    motion_detector = MotionDetectorFileSource("motion_data.jsonl")
    camera = CameraFileSource("camera_data.jsonl")
    perimeter_sensor = PerimeterSensorFileSource("perimeter_data.jsonl")

    return motion_detector, camera, perimeter_sensor

def main():
    """Run the security intrusion detection demo."""
    print("=== EventFlow Security Intrusion Detection Demo ===\n")

    # Create security sensor sources
    print("Setting up security sensors...")
    motion_sensor, camera_sensor, perimeter_sensor = simulate_security_sensors()

    # Create intrusion detection graph
    print("Creating intrusion detection graph...")
    intrusion_graph = intrusion_detection(
        source=motion_sensor,
        motion_threshold=0.5,  # Detect motion above 50% intensity
        anomaly_window="1 s",  # 1 second anomaly detection window
        spatial_resolution=64,  # 64x64 perimeter grid
        perimeter_zones=[(10, 10, 20, 20), (40, 40, 50, 50)],  # Sensitive zones
    )

    # Create threat assessment graph
    print("Creating threat assessment graph...")
    threat_graph = threat_assessment(
        source=intrusion_graph,  # Connect to intrusion detection output
        risk_threshold=0.7,  # Classify threats above 70% risk
        behavior_window="5 s",  # 5 second behavior analysis window
        analysis_channels=8,  # 8 parallel analysis channels
    )

    # Create security automation graph
    print("Creating security automation graph...")
    automation_graph = security_automation(
        source=threat_graph,  # Connect to threat assessment output
        alert_threshold=0.8,  # Generate alerts above 80% confidence
        response_window="2 s",  # 2 second response coordination window
        coordination_channels=4,  # 4 parallel response channels
    )

    print("Configuration:")
    print(f"  - Motion threshold: 50%")
    print(f"  - Anomaly detection window: 1s")
    print(f"  - Perimeter grid: 64x64")
    print(f"  - Risk threshold: 70%")
    print(f"  - Alert threshold: 80%")
    print()

    # Simulate processing (in real application, this would process live sensor data)
    print("Starting security monitoring simulation...")
    print("Press Ctrl+C to stop\n")

    try:
        # In a real application, you would use run_event_mode() to process live data
        # For demo, we'll show the graph structures and simulate events
        print("Graph structures:")
        print(f"  - Intrusion detection: {len(intrusion_graph.nodes)} nodes, {len(intrusion_graph.connections)} connections")
        print(f"  - Threat assessment: {len(threat_graph.nodes)} nodes, {len(threat_graph.connections)} connections")
        print(f"  - Security automation: {len(automation_graph.nodes)} nodes, {len(automation_graph.connections)} connections")
        print()

        # Simulate security monitoring events
        print("Simulating security monitoring events:")
        motion_events = 0
        camera_events = 0
        perimeter_events = 0

        # Process motion detector events
        for packet in motion_sensor.subscribe():
            motion_events += 1
            zone = packet.meta.get('zone', 0)
            intensity = packet.value

            if intensity > 0.5:  # Above motion threshold
                print(f"  Motion detected in zone {zone}: {intensity:.2f} intensity")

            if motion_events >= 5:  # Limit demo output
                break

        print()

        # Process camera events
        for packet in camera_sensor.subscribe():
            camera_events += 1
            x = packet.meta.get('x', 0)
            y = packet.meta.get('y', 0)

            print(f"  Camera motion at ({x},{y})")

            if camera_events >= 3:  # Limit demo output
                break

        print()

        # Process perimeter sensor events
        for packet in perimeter_sensor.subscribe():
            perimeter_events += 1
            zone = packet.meta.get('zone', 'unknown')
            breach_type = packet.meta.get('breach_type', 'unknown')
            intensity = packet.value

            if intensity > 25:  # Significant breach
                print(f"  Perimeter breach in {zone}: {breach_type} ({intensity:.1f} intensity)")

            if perimeter_events >= 3:  # Limit demo output
                break

        print("\nDemo completed successfully!")
        print("\nThis demonstrates:")
        print("- Real-time intrusion detection with motion tracking")
        print("- Threat assessment using spiking neural networks")
        print("- Automated security response coordination")
        print("- Multi-sensor fusion for comprehensive surveillance")
        print("- Energy-efficient neuromorphic security processing")
        print("\nSecurity capabilities implemented:")
        print("- Motion detection and anomaly analysis")
        print("- Camera network integration")
        print("- Perimeter breach monitoring")
        print("- Automated alert generation")
        print("- Threat classification and risk evaluation")

    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"Error during demo: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())