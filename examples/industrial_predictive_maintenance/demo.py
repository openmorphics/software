#!/usr/bin/env python3
"""
EventFlow Industrial Predictive Maintenance Demo

This example demonstrates predictive maintenance using anomaly detection
and equipment health monitoring with neuromorphic processing.
"""

import sys
import os

# Add the project root to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

try:
    from eventflow_sal.drivers.industrial import ProcessSensorFileSource
    from eventflow_core.eir.runtime import run_event_mode
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure EventFlow is properly installed or run from the repository root.")
    sys.exit(1)

try:
    from eventflow_modules.industrial import predictive_maintenance
except ImportError as e:
    print(f"Industrial module import error: {e}")
    print("The industrial module may not be properly installed.")
    sys.exit(1)

def main():
    print("EventFlow Industrial Predictive Maintenance Demo")
    print("=" * 55)

    # Create sensor sources for different equipment parameters
    temp_sensor = ProcessSensorFileSource("motor_temp.sim", sensor_type="temperature")
    current_sensor = ProcessSensorFileSource("motor_current.sim", sensor_type="current")
    vibration_sensor = ProcessSensorFileSource("motor_vibration.sim", sensor_type="generic")

    # Create predictive maintenance graph for motor monitoring
    pm_graph = predictive_maintenance(
        source=temp_sensor,  # Primary sensor for health assessment
        equipment_type="motor",
        failure_threshold=0.8,
        health_window="2 hours",
        anomaly_sensitivity=0.6
    )

    print(f"Created predictive maintenance graph with {len(pm_graph.nodes)} nodes")
    print("Equipment type: motor")
    print("Monitoring parameters: vibration, current, temperature")

    # Run predictive maintenance analysis
    print("\nRunning predictive maintenance analysis...")
    try:
        # Run for simulation period
        results = run_event_mode(pm_graph, max_steps=2000)

        print("Analysis complete!")
        print(f"Processed {len(results.get('health_assessment', []))} health assessment events")
        print(f"Detected {len(results.get('failure_prediction', []))} failure predictions")

        # Check for anomalies in different parameters
        anomaly_types = ['anomaly_vibration', 'anomaly_current', 'anomaly_temperature']
        total_anomalies = 0
        for anomaly_type in anomaly_types:
            count = len(results.get(anomaly_type, []))
            if count > 0:
                print(f"⚠️  {anomaly_type}: {count} anomalies detected")
                total_anomalies += count

        if total_anomalies == 0:
            print("✅ No anomalies detected - equipment appears healthy")
        else:
            print(f"⚠️  Total anomalies detected: {total_anomalies}")

        # Health assessment summary
        health_events = len(results.get('health_assessment', []))
        if health_events > 0:
            print(f"📊 Health assessment completed with {health_events} evaluations")

    except Exception as e:
        print(f"Error running predictive maintenance analysis: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())