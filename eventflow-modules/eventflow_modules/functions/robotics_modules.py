"""
Robotics functional modules.

This module provides specialized modules for robotic control and navigation
including obstacle avoidance, path planning, and motor control.
"""

from typing import Any, Dict, List, Union, Tuple
import numpy as np
from .base import ControlModule, AlgorithmModule


class ObstacleAvoidanceController(ControlModule):
    """
    Obstacle avoidance controller for robotic navigation.

    Uses sensor data to avoid obstacles and navigate safely.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR]
        caps.max_latency_ms = 50.0
        caps.real_time_capable = True
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = ["numpy", "scipy"]
        reqs.input_constraints = {"sensor_data": True, "spatial": True}
        reqs.output_constraints = {"control_commands": True, "safe_navigation": True}
        return reqs

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Process sensor data for obstacle avoidance.

        Args:
            inputs: Sensor data (LiDAR, ultrasonic, etc.)

        Returns:
            Control commands for obstacle avoidance
        """
        avoidance_method = self.config.get('method', 'potential_field')
        safety_margin = self.config.get('safety_margin', 0.5)  # meters
        max_speed = self.config.get('max_speed', 1.0)  # m/s

        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']

            if len(events) < 5:
                return {'control_commands': [], 'obstacles_detected': 0}

            if avoidance_method == 'potential_field':
                commands = self._potential_field_avoidance(events, safety_margin, max_speed)
            elif avoidance_method == 'vector_field':
                commands = self._vector_field_avoidance(events, safety_margin, max_speed)
            else:
                commands = self._simple_avoidance(events, safety_margin, max_speed)

            return {
                'control_commands': commands,
                'obstacles_detected': len([e for e in events if e.get('distance', float('inf')) < safety_margin]),
                'method': avoidance_method,
                'safety_margin': safety_margin
            }

        return inputs

    def _potential_field_avoidance(self, events: List[Dict[str, Any]], safety_margin: float, max_speed: float) -> List[Dict[str, Any]]:
        """Potential field-based obstacle avoidance"""
        commands = []

        # Calculate repulsive forces from obstacles
        repulsive_force_x = 0.0
        repulsive_force_y = 0.0

        obstacle_count = 0

        for event in events:
            distance = event.get('distance', float('inf'))
            angle = event.get('angle', 0)  # radians

            if distance < safety_margin and distance > 0:
                # Repulsive force inversely proportional to distance
                force_magnitude = 1.0 / (distance ** 2) if distance > 0.1 else 10.0

                # Force direction away from obstacle
                force_x = force_magnitude * np.cos(angle)
                force_y = force_magnitude * np.sin(angle)

                repulsive_force_x += force_x
                repulsive_force_y += force_y
                obstacle_count += 1

        if obstacle_count > 0:
            # Normalize repulsive force and limit speed
            total_force = np.sqrt(repulsive_force_x**2 + repulsive_force_y**2)
            if total_force > max_speed:
                repulsive_force_x = (repulsive_force_x / total_force) * max_speed
                repulsive_force_y = (repulsive_force_y / total_force) * max_speed

            commands.append({
                'type': 'velocity_command',
                'linear_x': repulsive_force_x,
                'linear_y': repulsive_force_y,
                'angular_z': 0.0,  # No rotation for now
                'timestamp': events[0].get('timestamp', 0)
            })

        return commands

    def _vector_field_avoidance(self, events: List[Dict[str, Any]], safety_margin: float, max_speed: float) -> List[Dict[str, Any]]:
        """Vector field histogram-based avoidance"""
        # Simplified VFH implementation
        commands = []

        # Create histogram of obstacle directions
        angle_bins = 36  # 10-degree bins
        histogram = np.zeros(angle_bins)

        for event in events:
            distance = event.get('distance', float('inf'))
            angle = event.get('angle', 0)

            if distance < safety_margin:
                # Convert angle to bin index
                bin_idx = int((angle + np.pi) / (2 * np.pi) * angle_bins) % angle_bins
                histogram[bin_idx] += 1.0 / (distance + 0.1)  # Weight by inverse distance

        # Find the direction with lowest obstacle density
        best_direction_idx = np.argmin(histogram)
        best_angle = (best_direction_idx / angle_bins) * 2 * np.pi - np.pi

        # Generate movement command toward safest direction
        speed = min(max_speed, max_speed * (1.0 - np.min(histogram) / np.max(histogram)))

        commands.append({
            'type': 'velocity_command',
            'linear_x': speed * np.cos(best_angle),
            'linear_y': speed * np.sin(best_angle),
            'angular_z': 0.0,
            'timestamp': events[0].get('timestamp', 0)
        })

        return commands

    def _simple_avoidance(self, events: List[Dict[str, Any]], safety_margin: float, max_speed: float) -> List[Dict[str, Any]]:
        """Simple threshold-based avoidance"""
        commands = []

        # Check for obstacles in front
        front_obstacles = [
            e for e in events
            if e.get('distance', float('inf')) < safety_margin and
            abs(e.get('angle', 0)) < np.pi / 4  # 45-degree cone in front
        ]

        if front_obstacles:
            # Turn away from obstacles
            turn_direction = 1.0 if np.random.rand() > 0.5 else -1.0  # Random turn direction

            commands.append({
                'type': 'velocity_command',
                'linear_x': max_speed * 0.5,  # Slow down
                'linear_y': 0.0,
                'angular_z': turn_direction * 0.5,  # Turn
                'timestamp': events[0].get('timestamp', 0)
            })
        else:
            # Clear path - move forward
            commands.append({
                'type': 'velocity_command',
                'linear_x': max_speed,
                'linear_y': 0.0,
                'angular_z': 0.0,
                'timestamp': events[0].get('timestamp', 0)
            })

        return commands


class PathPlanner(AlgorithmModule):
    """
    Path planning module for robotic navigation.

    Plans collision-free paths from start to goal positions.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR]
        caps.max_latency_ms = 200.0  # Path planning can take longer
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = ["numpy", "scipy"]
        reqs.input_constraints = {"map_data": True, "goal_position": True}
        reqs.output_constraints = {"path": True, "waypoints": True}
        return reqs

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Plan a path from current position to goal.

        Args:
            inputs: Map data, current position, goal position

        Returns:
            Planned path with waypoints
        """
        planning_algorithm = self.config.get('algorithm', 'astar')
        grid_resolution = self.config.get('grid_resolution', 0.1)  # meters

        if isinstance(inputs, dict):
            # Extract planning parameters
            start_pos = inputs.get('start_position', (0, 0))
            goal_pos = inputs.get('goal_position', (1, 1))
            obstacles = inputs.get('obstacles', [])

            if planning_algorithm == 'astar':
                path = self._astar_planning(start_pos, goal_pos, obstacles, grid_resolution)
            elif planning_algorithm == 'dijkstra':
                path = self._dijkstra_planning(start_pos, goal_pos, obstacles, grid_resolution)
            else:
                path = self._simple_planning(start_pos, goal_pos, obstacles)

            return {
                'path': path,
                'waypoints': len(path),
                'start_position': start_pos,
                'goal_position': goal_pos,
                'planning_algorithm': planning_algorithm,
                'path_length': self._calculate_path_length(path) if path else 0
            }

        return inputs

    def _astar_planning(self, start: Tuple[float, float], goal: Tuple[float, float],
                       obstacles: List[Tuple[float, float]], resolution: float) -> List[Tuple[float, float]]:
        """A* path planning algorithm"""
        # Simplified A* implementation (in practice would use a proper implementation)
        path = []

        # Create simple grid
        grid_size = 50
        grid = np.zeros((grid_size, grid_size))

        # Mark obstacles on grid
        for obs_x, obs_y in obstacles:
            grid_x = int(obs_x / resolution)
            grid_y = int(obs_y / resolution)
            if 0 <= grid_x < grid_size and 0 <= grid_y < grid_size:
                grid[grid_x, grid_y] = 1  # Obstacle

        # Convert start and goal to grid coordinates
        start_grid = (int(start[0] / resolution), int(start[1] / resolution))
        goal_grid = (int(goal[0] / resolution), int(goal[1] / resolution))

        # Simple straight-line path if no obstacles (simplified)
        if not obstacles:
            # Interpolate points between start and goal
            num_points = 10
            for i in range(num_points + 1):
                t = i / num_points
                x = start[0] + t * (goal[0] - start[0])
                y = start[1] + t * (goal[1] - start[1])
                path.append((x, y))
        else:
            # Very simplified obstacle avoidance
            path = [start, goal]  # Direct path for now

        return path

    def _dijkstra_planning(self, start: Tuple[float, float], goal: Tuple[float, float],
                          obstacles: List[Tuple[float, float]], resolution: float) -> List[Tuple[float, float]]:
        """Dijkstra path planning"""
        # Simplified implementation - same as A* for now
        return self._astar_planning(start, goal, obstacles, resolution)

    def _simple_planning(self, start: Tuple[float, float], goal: Tuple[float, float],
                        obstacles: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Simple direct path planning"""
        return [start, goal]

    def _calculate_path_length(self, path: List[Tuple[float, float]]) -> float:
        """Calculate total path length"""
        if len(path) < 2:
            return 0.0

        total_length = 0.0
        for i in range(len(path) - 1):
            dx = path[i+1][0] - path[i][0]
            dy = path[i+1][1] - path[i][1]
            total_length += np.sqrt(dx**2 + dy**2)

        return total_length


class MotorController(ControlModule):
    """
    Motor control module for robotic actuation.

    Controls motor speeds and positions with feedback.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR]
        caps.max_latency_ms = 10.0
        caps.real_time_capable = True
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = ["numpy"]
        reqs.input_constraints = {"control_inputs": True}
        reqs.output_constraints = {"motor_commands": True, "feedback": True}
        return reqs

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Generate motor control commands.

        Args:
            inputs: Desired velocities, positions, or control inputs

        Returns:
            Motor control commands with feedback
        """
        control_mode = self.config.get('control_mode', 'velocity')
        num_motors = self.config.get('num_motors', 4)
        max_speed = self.config.get('max_speed', 100.0)  # RPM or appropriate units

        if isinstance(inputs, dict):
            commands = []

            if control_mode == 'velocity':
                # Velocity control
                linear_x = inputs.get('linear_x', 0.0)
                linear_y = inputs.get('linear_y', 0.0)
                angular_z = inputs.get('angular_z', 0.0)

                # Convert to motor velocities (differential drive example)
                left_speed = linear_x - angular_z * 0.5
                right_speed = linear_x + angular_z * 0.5

                # Scale to motor limits
                left_speed = np.clip(left_speed, -max_speed, max_speed)
                right_speed = np.clip(right_speed, -max_speed, max_speed)

                commands.extend([
                    {
                        'motor_id': 0,  # Left motor
                        'command': left_speed,
                        'timestamp': inputs.get('timestamp', 0)
                    },
                    {
                        'motor_id': 1,  # Right motor
                        'command': right_speed,
                        'timestamp': inputs.get('timestamp', 0)
                    }
                ])

            elif control_mode == 'position':
                # Position control (simplified)
                target_positions = inputs.get('target_positions', [0.0] * num_motors)

                for i in range(min(num_motors, len(target_positions))):
                    commands.append({
                        'motor_id': i,
                        'command': target_positions[i],
                        'control_mode': 'position',
                        'timestamp': inputs.get('timestamp', 0)
                    })

            return {
                'motor_commands': commands,
                'control_mode': control_mode,
                'num_motors': len(commands),
                'max_speed': max_speed
            }

        return inputs