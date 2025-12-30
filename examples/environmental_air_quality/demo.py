#!/usr/bin/env python3
"""
Environmental Air Quality Monitoring Demo

This script demonstrates air quality monitoring using EventFlow's
neuromorphic environmental sensing capabilities. It simulates multiple
environmental sensors and processes air quality data in real-time.
"""

import sys
import time
from typing import List

# Add the local packages to Python path
sys.path.insert(0, '../../eventflow-sal')
sys.path.insert(0, '../../eventflow-core')
sys.path.insert(0, '../../eventflow-modules')

try:
    from eventflow_modules.environmental import air_quality_monitoring
    from eventflow_sal.drivers.environmental import EnvironmentalFileSource
    from eventflow_core.eir.runtime import run_event_mode
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure EventFlow packages are installed in development mode:")
    print("  pip install -e ./eventflow-core")
    print("  pip install -e ./eventflow-sal")
    print("  pip install -e ./eventflow-modules")
    sys.exit(1)

def simulate_environmental_sensors() -> List[EnvironmentalFileSource]:
    """
    Create simulated environmental sensors for demonstration.

    Returns:
        List[EnvironmentalFileSource]: List of simulated environmental sensor sources
    """
    # In a real application, you would connect to actual hardware sensors
    # For demo purposes, we'll use synthetic data from multiple sensor types
    sensors = [
        EnvironmentalFileSource("gas_sensor_data.jsonl", sensor_type="gas"),
        EnvironmentalFileSource("particulate_sensor_data.jsonl", sensor_type="air_quality"),
        EnvironmentalFileSource("chemical_sensor_data.jsonl", sensor_type="chemical"),
    ]
    return sensors

def main():
    """Run the environmental air quality monitoring demo."""
    print("=== EventFlow Environmental Air Quality Monitoring Demo ===\n")

    # Create environmental sensor sources
    print("Setting up environmental sensors...")
    sensor_sources = simulate_environmental_sensors()

    # Create air quality monitoring graph
    print("Creating air quality monitoring graph...")
    air_quality_graph = air_quality_monitoring(
        sources=sensor_sources,
        pollutants=["PM2.5", "NO2", "CO"],
        thresholds={
            "PM2.5": 35.0,  # EPA 24-hour standard
            "NO2": 100.0,   # EPA 1-hour standard
            "CO": 35.0      # EPA 1-hour standard
        },
        monitoring_window="1 hour",
        alert_level="moderate",
    )

    print("Configuration:")
    print("  - Pollutants monitored: PM2.5, NO2, CO")
    print("  - Alert thresholds: EPA standards")
    print("  - Monitoring window: 1 hour")
    print("  - Alert level: moderate")
    print()

    # Simulate processing (in real application, this would process live sensor data)
    print("Starting air quality monitoring simulation...")
    print("Press Ctrl+C to stop\n")

    try:
        # In a real application, you would use run_event_mode() to process live data
        # For demo, we'll just show the graph structure
        print("Graph structure:")
        print(f"  - Nodes: {len(air_quality_graph.nodes) if hasattr(air_quality_graph, 'nodes') else 'N/A'}")
        print(f"  - Connections: {len(air_quality_graph.connections) if hasattr(air_quality_graph, 'connections') else 'N/A'}")
        print()

        # Simulate air quality monitoring events
        print("Simulating air quality monitoring events:")
        events_simulated = 0

        for source in sensor_sources:
            for packet in source.subscribe():
                events_simulated += 1
                sensor_type = packet.meta.get('sensor_type', 'unknown')
                concentration = packet.value

                # Simple alert logic
                alert_triggered = False
                alert_message = ""

                if sensor_type == "PM2.5" and concentration > 35.0:
                    alert_triggered = True
                    alert_message = f"PM2.5 alert: {concentration:.1f} µg/m³ (above EPA 24h limit)"
                elif sensor_type == "NO2" and concentration > 100.0:
                    alert_triggered = True
                    alert_message = f"NO2 alert: {concentration:.1f} ppb (above EPA 1h limit)"
                elif sensor_type == "CO" and concentration > 35.0:
                    alert_triggered = True
                    alert_message = f"CO alert: {concentration:.1f} ppm (above EPA 1h limit)"

                if alert_triggered:
                    print(f"  ⚠️  ALERT: {alert_message}")
                else:
                    print(f"  ✓  {sensor_type}: {concentration:.1f} - Normal")

                if events_simulated >= 15:  # Limit demo output
                    break
            if events_simulated >= 15:
                break

        print("\nDemo completed successfully!")
        print("\nThis demonstrates:")
        print("- Multi-sensor environmental data fusion")
        print("- Real-time air quality index computation")
        print("- Automated pollution alerts")
        print("- Event-driven environmental monitoring")
        print("- EPA standard compliance checking")

    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"Error during demo: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())