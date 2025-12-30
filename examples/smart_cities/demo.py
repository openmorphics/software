#!/usr/bin/env python3
"""Smart Cities IoT Demonstration

Demonstrates real-time urban monitoring using EventFlow's smart cities module
with neuromorphic computing for energy-efficient city management.
"""

import argparse
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from eventflow_sal import open as sal_open
from eventflow_core.eir.serialize import graph_to_json
from eventflow_modules.smart_cities import (
    traffic_monitoring,
    crowd_analysis,
    environmental_monitoring,
    infrastructure_health
)

def demo_traffic_monitoring():
    """Demonstrate real-time traffic monitoring."""
    print("🚗 Smart Cities: Traffic Monitoring Demo")
    print("=" * 50)

    # Create traffic monitoring graph
    graph = traffic_monitoring(
        source="city.traffic://demo_camera",
        detection_threshold=0.3,
        congestion_window="30 s",
        spatial_resolution=(64, 64)
    )

    print(f"📊 Created traffic monitoring graph with {len(graph.nodes)} nodes")
    print("🎯 Monitoring vehicle movement patterns for congestion analysis")

    # Simulate traffic data processing
    source = sal_open("city.traffic://demo_camera")
    event_count = 0

    print("\n📡 Processing traffic events...")
    for packet in source.subscribe():
        event_count += 1
        if event_count <= 10:  # Show first 10 events
            print(f"🚗 Traffic event: channel={packet.channel}, value={packet.value:.1f}, meta={packet.meta}")
        elif event_count == 11:
            print("... (processing more events)")
        elif event_count >= 100:  # Stop after 100 events
            break

        time.sleep(0.01)  # Simulate real-time processing

    print(f"✅ Processed {event_count} traffic events")
    print("💡 Traffic monitoring enables real-time congestion detection for smart signals")

def demo_environmental_monitoring():
    """Demonstrate urban environmental sensing."""
    print("🌱 Smart Cities: Environmental Monitoring Demo")
    print("=" * 50)

    # Create environmental monitoring graph
    graph = environmental_monitoring(
        source="city.pollution://demo_network",
        pollution_threshold=0.6,
        noise_threshold=0.7,
        monitoring_window="15 min",
        sensor_count=8
    )

    print(f"📊 Created environmental monitoring graph with {len(graph.nodes)} nodes")
    print("🎯 Monitoring air quality and noise pollution across urban zones")

    # Simulate environmental data processing
    source = sal_open("city.pollution://demo_network")
    event_count = 0

    print("\n📡 Processing environmental events...")
    for packet in source.subscribe():
        event_count += 1
        if event_count <= 10:  # Show first 10 events
            print(f"🌱 Environmental event: channel={packet.channel}, value={packet.value:.1f}, meta={packet.meta}")
        elif event_count == 11:
            print("... (processing more events)")
        elif event_count >= 100:  # Stop after 100 events
            break

        time.sleep(0.01)  # Simulate real-time processing

    print(f"✅ Processed {event_count} environmental events")
    print("💡 Environmental monitoring enables pollution alerts and air quality optimization")

def demo_crowd_analysis():
    """Demonstrate urban crowd analysis."""
    print("👥 Smart Cities: Crowd Analysis Demo")
    print("=" * 50)

    # Create crowd analysis graph
    graph = crowd_analysis(
        source="city.crowd://demo_sensors",
        density_threshold=0.5,
        analysis_window="30 s",
        spatial_resolution=(32, 32)
    )

    print(f"📊 Created crowd analysis graph with {len(graph.nodes)} nodes")
    print("🎯 Analyzing pedestrian density for urban mobility management")

    # Simulate crowd data processing
    source = sal_open("city.crowd://demo_sensors")
    event_count = 0

    print("\n📡 Processing crowd events...")
    for packet in source.subscribe():
        event_count += 1
        if event_count <= 10:  # Show first 10 events
            print(f"👥 Crowd event: channel={packet.channel}, value={packet.value:.1f}, meta={packet.meta}")
        elif event_count == 11:
            print("... (processing more events)")
        elif event_count >= 100:  # Stop after 100 events
            break

        time.sleep(0.01)  # Simulate real-time processing

    print(f"✅ Processed {event_count} crowd events")
    print("💡 Crowd analysis enables public safety monitoring and event management")

def demo_infrastructure_health():
    """Demonstrate structural health monitoring."""
    print("🏗️ Smart Cities: Infrastructure Health Demo")
    print("=" * 50)

    # Create infrastructure health graph
    graph = infrastructure_health(
        source="city.infrastructure://demo_monitor",
        vibration_threshold=0.4,
        stress_threshold=0.5,
        monitoring_window="1 hour",
        sensor_points=16
    )

    print(f"📊 Created infrastructure health graph with {len(graph.nodes)} nodes")
    print("🎯 Monitoring structural integrity for predictive maintenance")

    # Simulate infrastructure data processing
    source = sal_open("city.infrastructure://demo_monitor")
    event_count = 0

    print("\n📡 Processing infrastructure events...")
    for packet in source.subscribe():
        event_count += 1
        if event_count <= 10:  # Show first 10 events
            print(f"🏗️ Infrastructure event: channel={packet.channel}, value={packet.value:.1f}, meta={packet.meta}")
        elif event_count == 11:
            print("... (processing more events)")
        elif event_count >= 100:  # Stop after 100 events
            break

        time.sleep(0.01)  # Simulate real-time processing

    print(f"✅ Processed {event_count} infrastructure events")
    print("💡 Infrastructure monitoring enables predictive maintenance and safety alerts")

def demo_eir_generation():
    """Demonstrate EIR graph generation for CLI integration."""
    print("📋 Smart Cities: EIR Graph Generation Demo")
    print("=" * 50)

    # Create all smart cities graphs
    graphs = {
        "traffic": traffic_monitoring("city.traffic://camera"),
        "crowd": crowd_analysis("city.crowd://sensors"),
        "environment": environmental_monitoring("city.pollution://network"),
        "infrastructure": infrastructure_health("city.infrastructure://monitor")
    }

    for name, graph in graphs.items():
        # Convert to EIR JSON format
        eir_json = graph_to_json(graph)
        print(f"📄 Generated EIR for {name} monitoring: {len(eir_json)} chars")

        # Save to file for CLI testing
        filename = f"smart_cities_{name}.eir"
        with open(filename, 'w') as f:
            f.write(eir_json)
        print(f"💾 Saved {filename}")

    print("🔧 EIR graphs ready for CLI: ef validate, ef profile, ef run")
    print("⚡ Use EF_NATIVE=1 for native acceleration on neuromorphic hardware")

def main():
    parser = argparse.ArgumentParser(description="Smart Cities IoT Demonstration")
    parser.add_argument("--app", choices=["traffic", "environment", "crowd", "infrastructure", "eir"],
                       help="Smart cities application to demonstrate")
    parser.add_argument("--all", action="store_true",
                       help="Run all demonstrations")

    args = parser.parse_args()

    print("🏙️ EventFlow Smart Cities IoT Demonstration")
    print("Using neuromorphic computing for energy-efficient urban management\n")

    if args.all or args.app == "traffic":
        demo_traffic_monitoring()
        print()

    if args.all or args.app == "environment":
        demo_environmental_monitoring()
        print()

    if args.all or args.app == "crowd":
        demo_crowd_analysis()
        print()

    if args.all or args.app == "infrastructure":
        demo_infrastructure_health()
        print()

    if args.all or args.app == "eir":
        demo_eir_generation()
        print()

    if not args.app and not args.all:
        print("Please specify --app [traffic|environment|crowd|infrastructure|eir] or --all")
        return 1

    print("🎉 Smart Cities demonstration complete!")
    print("💡 EventFlow enables energy-efficient neuromorphic processing for urban IoT")

    return 0

if __name__ == "__main__":
    sys.exit(main())