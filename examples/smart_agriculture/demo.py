#!/usr/bin/env python3
"""
Smart Agriculture Crop Monitoring Demo

This script demonstrates precision farming capabilities using EventFlow's
smart agriculture module. It shows crop health assessment through NDVI
analysis and growth tracking for sustainable farming applications.
"""

import sys
import time
from typing import List

# Add the local packages to Python path
sys.path.insert(0, '../../eventflow-sal')
sys.path.insert(0, '../../eventflow-core')
sys.path.insert(0, '../../eventflow-modules')

try:
    from eventflow_modules.smart_agriculture import crop_health_assessment, ndvi_analysis, growth_tracking
    from eventflow_sal.drivers.agriculture import CropSensorFileSource, WeatherFileSource
    from eventflow_core.eir.runtime import run_event_mode
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure EventFlow packages are installed in development mode:")
    print("  pip install -e ./eventflow-core")
    print("  pip install -e ./eventflow-sal")
    print("  pip install -e ./eventflow-modules")
    sys.exit(1)

def simulate_crop_sensor() -> CropSensorFileSource:
    """
    Create a simulated crop sensor for demonstration.

    Returns:
        CropSensorFileSource: Simulated multispectral crop sensor source
    """
    # In a real application, you would connect to actual agricultural sensors
    # For demo purposes, we'll use synthetic NDVI data
    return CropSensorFileSource("crop_data.jsonl")

def simulate_weather_sensor() -> WeatherFileSource:
    """
    Create a simulated weather station for demonstration.

    Returns:
        WeatherFileSource: Simulated weather station source
    """
    return WeatherFileSource("weather_data.jsonl")

def main():
    """Run the smart agriculture crop monitoring demo."""
    print("=== EventFlow Smart Agriculture Crop Monitoring Demo ===\n")

    # Create sensor sources
    print("Setting up agricultural sensors...")
    crop_source = simulate_crop_sensor()
    weather_source = simulate_weather_sensor()

    # Create crop health assessment graph
    print("Creating crop health assessment graph...")
    health_graph = crop_health_assessment(
        source=crop_source,
        ndvi_threshold=0.4,  # Healthy vegetation threshold
        window="24 h",  # Daily health assessment
        spatial_resolution=64,  # Field grid resolution
    )

    # Create NDVI analysis graph
    print("Creating NDVI analysis graph...")
    ndvi_graph = ndvi_analysis(
        source=crop_source,
        red_band=0,
        nir_band=1,
        smoothing_window="6 h",
    )

    # Create growth tracking graph
    print("Creating growth tracking graph...")
    growth_graph = growth_tracking(
        source=crop_source,
        height_threshold=0.05,  # 5cm growth detection
        growth_window="7 d",  # Weekly growth assessment
        canopy_resolution=32,
    )

    print("Configuration:")
    print(f"  - NDVI threshold: 0.4")
    print(f"  - Growth threshold: 5cm")
    print(f"  - Assessment windows: 24h health, 6h NDVI, 7d growth")
    print(f"  - Spatial resolution: 64x64 field grid")
    print()

    # Simulate processing
    print("Starting crop monitoring simulation...")
    print("Press Ctrl+C to stop\n")

    try:
        print("Graph structures:")
        print(f"  - Health assessment: {len(health_graph.nodes)} nodes")
        print(f"  - NDVI analysis: {len(ndvi_graph.nodes)} nodes")
        print(f"  - Growth tracking: {len(growth_graph.nodes)} nodes")
        print()

        # Simulate crop monitoring events
        print("Simulating crop health monitoring:")
        events_processed = 0
        healthy_readings = 0
        growth_events = 0

        for packet in crop_source.subscribe():
            events_processed += 1
            x = packet.meta.get('x', 0)
            y = packet.meta.get('y', 0)
            ndvi_value = packet.value

            # Assess health based on NDVI
            if ndvi_value >= 0.4:
                healthy_readings += 1
                print(f"  Healthy vegetation at ({x},{y}): NDVI={ndvi_value:.3f}")
            else:
                print(f"  Stressed vegetation at ({x},{y}): NDVI={ndvi_value:.3f}")

            # Simulate growth detection (simplified)
            if events_processed % 10 == 0 and ndvi_value > 0.5:
                growth_events += 1
                print(f"  Growth detected in region ({x},{y})")

            if events_processed >= 20:  # Limit demo output
                break

        print("\nSimulation Summary:")
        print(f"  - Events processed: {events_processed}")
        print(f"  - Healthy readings: {healthy_readings} ({healthy_readings/events_processed*100:.1f}%)")
        print(f"  - Growth events: {growth_events}")
        print()

        print("Demo completed successfully!")
        print("\nThis demonstrates:")
        print("- Precision farming with NDVI-based crop health assessment")
        print("- Real-time vegetation monitoring")
        print("- Growth tracking for yield optimization")
        print("- Event-driven agricultural data processing")
        print("- Neuromorphic computing for energy-efficient farm management")

    except KeyboardInterrupt:
        print("\nDemo interrupted by user.")
    except Exception as e:
        print(f"Error during demo: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())