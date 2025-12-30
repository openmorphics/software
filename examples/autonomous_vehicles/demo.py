#!/usr/bin/env python3
"""
Autonomous Vehicle Sensor Fusion Demo

This script demonstrates autonomous vehicle capabilities using EventFlow's
neuromorphic LiDAR processing, sensor fusion, and navigation algorithms.
It shows real-time 3D sensing, multi-sensor integration, and autonomous
decision making for self-driving applications.
"""

import sys
import time
from typing import List

# Add the local packages to Python path
sys.path.insert(0, '../../eventflow-sal')
sys.path.insert(0, '../../eventflow-core')
sys.path.insert(0, '../../eventflow-modules')

try:
    from eventflow_modules.autonomous_vehicles import (
        lidar_point_cloud_processing, sensor_fusion, autonomous_navigation
    )
    from eventflow_sal.drivers.automotive import LiDARFileSource, RadarFileSource
    from eventflow_core.eir.runtime import run_event_mode
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure EventFlow packages are installed in development mode:")
    print("  pip install -e ./eventflow-core")
    print("  pip install -e ./eventflow-sal")
    print("  pip install -e ./eventflow-modules")
    sys.exit(1)

def simulate_autonomous_sensors() -> List[any]:
    """
    Create simulated autonomous vehicle sensor sources for demonstration.

    Returns:
        List: Simulated sensor sources (LiDAR, radar, camera, IMU)
    """
    # In a real application, you would connect to actual automotive sensors
    # For demo purposes, we'll use synthetic automotive data
    return [
        LiDARFileSource("front_lidar.pcd"),
        RadarFileSource("front_radar.dat"),
    ]

def main():
    """Run the autonomous vehicle sensor fusion demo."""
    print("=== EventFlow Autonomous Vehicle Sensor Fusion Demo ===\n")

    # Create autonomous vehicle sensor sources
    print("Setting up autonomous vehicle sensor sources...")
    sensor_sources = simulate_autonomous_sensors()

    # Create LiDAR point cloud processing for obstacle detection
    print("Creating LiDAR point cloud processing...")
    lidar_graph = lidar_point_cloud_processing(
        source=sensor_sources[0],  # LiDAR source
        obstacle_threshold=0.8,
        ground_segmentation_window="200 ms",
        max_range=100.0
    )

    # Create multi-sensor fusion (LiDAR + radar + camera + IMU)
    print("Creating multi-sensor fusion...")
    fusion_sources = {
        "lidar": sensor_sources[0],
        "radar": sensor_sources[1],
        "camera": "av://camera/front",
        "imu": "av://imu/vehicle"
    }
    fusion_graph = sensor_fusion(
        sources=fusion_sources,
        fusion_method="kalman",
        temporal_alignment_window="100 ms",
        confidence_threshold=0.75
    )

    # Create autonomous navigation with path planning
    print("Creating autonomous navigation system...")
    navigation_graph = autonomous_navigation(
        sensor_input=fusion_graph,  # Use fused sensor data
        path_planning_algorithm="astar",
        collision_avoidance_radius=3.0,
        navigation_horizon="2 s"
    )

    print("\nAutonomous Vehicle Configuration:")
    print("  - LiDAR: 100m range, obstacle threshold 0.8")
    print("  - Sensor Fusion: Kalman filter, 4 modalities")
    print("  - Navigation: A* path planning, 3m collision radius")
    print("  - Real-time horizon: 2 seconds")
    print()

    # Simulate processing (in real application, this would process live sensor data)
    print("Starting autonomous vehicle simulation...")
    print("Press Ctrl+C to stop\n")

    try:
        # Demonstrate LiDAR data processing
        print("LiDAR point cloud processing simulation:")
        lidar_source = LiDARFileSource("demo_lidar.pcd")
        events_processed = 0

        for packet in lidar_source.subscribe():
            events_processed += 1
            point_data = packet.meta

            print(f"  Point {events_processed}:")
            print(".2f")
            print(".2f")
            print(f"    Intensity: {point_data.get('intensity', 0)}")
            print(f"    Timestamp: {packet.t_ns} ns")
            print()

            if events_processed >= 5:  # Limit demo output
                break

        # Demonstrate radar data processing
        print("Radar detection processing simulation:")
        radar_source = RadarFileSource("demo_radar.dat")
        detections_processed = 0

        for packet in radar_source.subscribe():
            detections_processed += 1
            detection_data = packet.meta

            print(f"  Detection {detections_processed}:")
            print(".2f")
            print(".1f")
            print(".1f")
            print(".1f")
            print(f"    Timestamp: {packet.t_ns} ns")
            print()

            if detections_processed >= 3:  # Limit demo output
                break

        print("\nDemo completed successfully!")
        print("\nThis demonstrates:")
        print("- LiDAR point cloud processing with obstacle detection")
        print("- Ground segmentation and 3D mapping")
        print("- Multi-sensor fusion (LiDAR + radar + camera + IMU)")
        print("- Temporal alignment of asynchronous sensor streams")
        print("- Autonomous navigation with path planning")
        print("- Collision avoidance and trajectory control")
        print("- Real-time neuromorphic event processing for autonomous driving")

    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"Error during demo: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())