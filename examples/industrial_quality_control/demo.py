#!/usr/bin/env python3
"""
EventFlow Industrial Quality Control Demo

This example demonstrates quality control monitoring for manufacturing
processes using neuromorphic processing for real-time defect detection.
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
    from eventflow_modules.industrial import quality_control
except ImportError as e:
    print(f"Industrial module import error: {e}")
    print("The industrial module may not be properly installed.")
    sys.exit(1)

def main():
    print("EventFlow Industrial Quality Control Demo")
    print("=" * 50)

    # Create sensor sources for machining process monitoring
    speed_sensor = ProcessSensorFileSource("machining_speed.sim", sensor_type="speed")
    force_sensor = ProcessSensorFileSource("machining_force.sim", sensor_type="force")

    # Define control limits for machining process
    control_limits = {
        "speed": {"upper": 1500, "lower": 1200},  # RPM
        "force": {"upper": 500, "lower": 300}    # Newtons
    }

    # Create quality control graph for machining process
    qc_graph = quality_control(
        source=speed_sensor,  # Primary sensor for quality monitoring
        process_type="machining",
        defect_threshold=0.05,
        parameter_tolerance=0.1,
        monitoring_window="30 s",
        control_limits=control_limits
    )

    print(f"Created quality control graph with {len(qc_graph.nodes)} nodes")
    print("Process type: machining")
    print("Monitored parameters: speed, feed, depth")
    print(f"Control limits defined for: {list(control_limits.keys())}")

    # Run quality control analysis
    print("\nRunning quality control analysis...")
    try:
        # Run for simulation period
        results = run_event_mode(qc_graph, max_steps=1500)

        print("Analysis complete!")
        print(f"Processed {len(results.get('quality_assessment', []))} quality assessments")

        # Check for defects and parameter deviations
        defects = len(results.get('defect_detection', []))
        if defects > 0:
            print(f"⚠️  Detected {defects} quality defects")

        # Check control limit violations
        for param in control_limits.keys():
            upper_violations = len(results.get(f'upper_{param}', []))
            lower_violations = len(results.get(f'lower_{param}', []))
            if upper_violations > 0 or lower_violations > 0:
                print(f"⚠️  {param}: {upper_violations} upper, {lower_violations} lower limit violations")

        # Check parameter control status
        control_params = ['control_speed', 'control_feed', 'control_depth']
        total_deviations = 0
        for param in control_params:
            deviations = len(results.get(param, []))
            if deviations > 0:
                print(f"⚠️  {param}: {deviations} parameter deviations")
                total_deviations += deviations

        # Overall quality assessment
        quality_events = len(results.get('quality_assessment', []))
        if quality_events > 0:
            print(f"✅ Quality assessment completed with {quality_events} evaluations")

        if defects == 0 and total_deviations == 0:
            print("✅ No quality issues detected - process appears in control")
        else:
            print(f"⚠️  Total quality issues: {defects + total_deviations}")

    except Exception as e:
        print(f"Error running quality control analysis: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())