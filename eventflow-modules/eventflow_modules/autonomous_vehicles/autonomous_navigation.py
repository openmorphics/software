from __future__ import annotations
from typing import Optional, Dict, Any
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, XYToChannel
import json
from ..errors import AutonomousError

# Optional Rust acceleration for autonomous processing
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore

def autonomous_navigation(
    sensor_input: Any,
    path_planning_algorithm: str = "astar",
    collision_avoidance_radius: float = 2.0,
    navigation_horizon: str = "5 s",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Autonomous navigation with path planning and collision avoidance.

    Implements real-time path planning and collision avoidance for autonomous vehicles
    using event-based sensor processing and neuromorphic decision making.

    Args:
        sensor_input: Fused sensor data input (SAL URI or event stream)
        path_planning_algorithm: Algorithm for path planning ("astar", "dijkstra", "rrt")
        collision_avoidance_radius: Minimum safe distance from obstacles (meters)
        navigation_horizon: Planning horizon for path computation
        params: Additional navigation parameters

    Returns:
        EIRGraph: Configured autonomous navigation processing graph

    Raises:
        AutonomousError: If navigation parameters or sensor input are invalid
    """
    valid_algorithms = ["astar", "dijkstra", "rrt"]
    if path_planning_algorithm not in valid_algorithms:
        raise AutonomousError(f"Path planning algorithm must be one of {valid_algorithms}, got {path_planning_algorithm}")

    if not isinstance(collision_avoidance_radius, (int, float)) or not (0.5 <= collision_avoidance_radius <= 10.0):
        raise AutonomousError(f"Collision avoidance radius must be between 0.5 and 10.0 meters, got {collision_avoidance_radius}")

    # Create EIR graph for autonomous navigation
    graph = EIRGraph(name="autonomous_navigation")

    # Input node for fused sensor data
    graph.add_source("sensor_input", sensor_input)

    # Obstacle map generation
    obstacle_map = graph.add_op(
        "obstacle_mapping",
        {
            "collision_radius": collision_avoidance_radius,
        }
    )

    # Path planning operation
    path_planner = graph.add_op(
        "path_planning",
        {
            "algorithm": path_planning_algorithm,
            "horizon": navigation_horizon,
        }
    )

    # Trajectory control
    trajectory_control = graph.add_op(
        "trajectory_control",
        {
            "control_horizon": "1 s",
        }
    )

    # Connect nodes
    graph.connect("sensor_input", obstacle_map)
    graph.connect(obstacle_map, path_planner)
    graph.connect(path_planner, trajectory_control)

    # Optional native acceleration
    if _ef_native_enabled():
        graph.enable_native_acceleration()

    return graph