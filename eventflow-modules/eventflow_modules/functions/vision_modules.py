"""
Vision processing functional modules.

This module provides specialized modules for computer vision tasks
including optical flow, object tracking, and feature detection.
"""

from typing import Any, Dict, List, Union, Tuple
import numpy as np
from .base import AlgorithmModule


class OpticalFlowEstimator(AlgorithmModule):
    """
    Optical flow estimation module using event-based methods.

    Estimates motion between consecutive frames using event data.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR]
        caps.max_latency_ms = 50.0
        caps.real_time_capable = True
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = ["numpy", "scipy"]
        reqs.input_constraints = {"temporal": True, "spatial": True}
        reqs.output_constraints = {"flow_vectors": True}
        return reqs

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Estimate optical flow from event streams.

        Args:
            inputs: Event data with spatial-temporal information

        Returns:
            Optical flow vectors and motion estimates
        """
        flow_method = self.config.get('flow_method', 'block_matching')
        search_radius = self.config.get('search_radius', 5)

        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']

            if len(events) < 10:
                return {'flow_vectors': [], 'motion_detected': False}

            # Group events into temporal windows
            time_windows = self._temporal_binning(events, window_ms=100)

            if len(time_windows) < 2:
                return {'flow_vectors': [], 'motion_detected': False}

            flow_vectors = []

            # Calculate flow between consecutive windows
            for i in range(len(time_windows) - 1):
                current_events = time_windows[i]
                next_events = time_windows[i + 1]

                if flow_method == 'block_matching':
                    vectors = self._block_matching_flow(current_events, next_events, search_radius)
                elif flow_method == 'event_correlation':
                    vectors = self._correlation_flow(current_events, next_events)
                else:
                    vectors = []

                flow_vectors.extend(vectors)

            return {
                'flow_vectors': flow_vectors,
                'motion_detected': len(flow_vectors) > 0,
                'total_events': len(events),
                'flow_method': flow_method
            }

        return inputs

    def _temporal_binning(self, events: List[Dict[str, Any]], window_ms: int) -> List[List[Dict[str, Any]]]:
        """Group events into temporal windows"""
        if not events:
            return []

        # Convert window_ms to nanoseconds
        window_ns = window_ms * 1000000

        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.get('timestamp', 0))
        min_time = sorted_events[0]['timestamp']

        windows = []
        current_window = []

        for event in sorted_events:
            window_idx = (event['timestamp'] - min_time) // window_ns

            if len(windows) <= window_idx:
                windows.extend([[] for _ in range(window_idx - len(windows) + 1)])

            windows[window_idx].append(event)

        return windows

    def _block_matching_flow(self, current_events: List[Dict[str, Any]],
                           next_events: List[Dict[str, Any]], radius: int) -> List[Dict[str, Any]]:
        """Calculate optical flow using block matching"""
        flow_vectors = []

        for curr_event in current_events:
            cx, cy = curr_event.get('x', 0), curr_event.get('y', 0)

            # Find best matching event in next frame within search radius
            best_match = None
            min_distance = float('inf')

            for next_event in next_events:
                nx, ny = next_event.get('x', 0), next_event.get('y', 0)

                # Check if within search radius
                if abs(nx - cx) <= radius and abs(ny - cy) <= radius:
                    distance = np.sqrt((nx - cx)**2 + (ny - cy)**2)
                    if distance < min_distance:
                        min_distance = distance
                        best_match = next_event

            if best_match:
                flow_vector = {
                    'x': cx,
                    'y': cy,
                    'flow_x': best_match['x'] - cx,
                    'flow_y': best_match['y'] - cy,
                    'magnitude': np.sqrt((best_match['x'] - cx)**2 + (best_match['y'] - cy)**2),
                    'timestamp': curr_event.get('timestamp', 0)
                }
                flow_vectors.append(flow_vector)

        return flow_vectors

    def _correlation_flow(self, current_events: List[Dict[str, Any]],
                         next_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate optical flow using correlation methods"""
        # Simplified correlation-based flow estimation
        flow_vectors = []

        # Calculate centroid motion as simple flow estimate
        if current_events and next_events:
            curr_centroid = self._calculate_centroid(current_events)
            next_centroid = self._calculate_centroid(next_events)

            if curr_centroid and next_centroid:
                flow_vector = {
                    'x': curr_centroid[0],
                    'y': curr_centroid[1],
                    'flow_x': next_centroid[0] - curr_centroid[0],
                    'flow_y': next_centroid[1] - curr_centroid[1],
                    'magnitude': np.sqrt((next_centroid[0] - curr_centroid[0])**2 +
                                       (next_centroid[1] - curr_centroid[1])**2),
                    'timestamp': current_events[0].get('timestamp', 0)
                }
                flow_vectors.append(flow_vector)

        return flow_vectors

    def _calculate_centroid(self, events: List[Dict[str, Any]]) -> Tuple[float, float]:
        """Calculate centroid of events"""
        if not events:
            return None

        x_sum = sum(e.get('x', 0) for e in events)
        y_sum = sum(e.get('y', 0) for e in events)

        return (x_sum / len(events), y_sum / len(events))


class CornerDetector(AlgorithmModule):
    """
    Corner and feature detection module for event-based cameras.

    Detects corners and interest points in event streams.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR]
        caps.max_latency_ms = 75.0
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = ["numpy", "scipy"]
        reqs.input_constraints = {"spatial": True, "temporal": True}
        reqs.output_constraints = {"corners": True, "features": True}
        return reqs

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Detect corners and features in event streams.

        Args:
            inputs: Event data with spatial coordinates

        Returns:
            Detected corners and feature points
        """
        detection_method = self.config.get('detection_method', 'harris')
        threshold = self.config.get('corner_threshold', 0.1)

        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']

            if len(events) < 20:
                return {'corners': [], 'features': []}

            # Create spatial histogram of events
            spatial_map = self._create_spatial_density_map(events)

            corners = []

            if detection_method == 'harris':
                corners = self._harris_corner_detection(spatial_map, threshold)
            elif detection_method == 'fast':
                corners = self._fast_corner_detection(events, threshold)
            else:
                corners = self._simple_corner_detection(spatial_map, threshold)

            # Convert corners back to event format
            corner_events = []
            for corner in corners:
                corner_event = {
                    'x': corner['x'],
                    'y': corner['y'],
                    'amplitude': corner.get('strength', 1.0),
                    'timestamp': events[0].get('timestamp', 0) if events else 0,
                    'corner_strength': corner.get('strength', 0),
                    'feature_type': 'corner'
                }
                corner_events.append(corner_event)

            return {
                'corners': corner_events,
                'features': corner_events,  # For compatibility
                'total_corners': len(corner_events),
                'detection_method': detection_method
            }

        return inputs

    def _create_spatial_density_map(self, events: List[Dict[str, Any]],
                                   grid_size: int = 16) -> np.ndarray:
        """Create spatial density map of events"""
        if not events:
            return np.zeros((grid_size, grid_size))

        # Find spatial bounds
        x_coords = [e.get('x', 0) for e in events]
        y_coords = [e.get('y', 0) for e in events]

        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)

        # Create density map
        density_map = np.zeros((grid_size, grid_size))

        for event in events:
            x, y = event.get('x', 0), event.get('y', 0)

            # Normalize to grid coordinates
            if x_max > x_min and y_max > y_min:
                grid_x = int((x - x_min) / (x_max - x_min) * (grid_size - 1))
                grid_y = int((y - y_min) / (y_max - y_min) * (grid_size - 1))

                grid_x = np.clip(grid_x, 0, grid_size - 1)
                grid_y = np.clip(grid_y, 0, grid_size - 1)

                density_map[grid_y, grid_x] += 1

        return density_map

    def _harris_corner_detection(self, density_map: np.ndarray, threshold: float) -> List[Dict[str, Any]]:
        """Harris corner detection on density map"""
        corners = []

        # Simple Harris corner response (simplified implementation)
        from scipy import ndimage

        # Compute gradients
        dx = ndimage.sobel(density_map, axis=1)
        dy = ndimage.sobel(density_map, axis=0)

        # Compute Harris response
        dx2 = dx * dx
        dy2 = dy * dy
        dxy = dx * dy

        # Gaussian smoothing
        dx2_smooth = ndimage.gaussian_filter(dx2, sigma=1)
        dy2_smooth = ndimage.gaussian_filter(dy2, sigma=1)
        dxy_smooth = ndimage.gaussian_filter(dxy, sigma=1)

        # Harris response
        det = dx2_smooth * dy2_smooth - dxy_smooth * dxy_smooth
        trace = dx2_smooth + dy2_smooth
        harris_response = det - 0.04 * trace * trace

        # Find local maxima above threshold
        from scipy.ndimage import maximum_filter
        local_max = (harris_response == maximum_filter(harris_response, size=3)) & (harris_response > threshold)

        y_coords, x_coords = np.where(local_max)

        for y, x in zip(y_coords, x_coords):
            corners.append({
                'x': int(x),
                'y': int(y),
                'strength': float(harris_response[y, x])
            })

        return corners

    def _fast_corner_detection(self, events: List[Dict[str, Any]], threshold: float) -> List[Dict[str, Any]]:
        """FAST corner detection on events"""
        # Simplified FAST-like corner detection
        corners = []

        for event in events:
            x, y = event.get('x', 0), event.get('y', 0)

            # Check if this event is a corner by looking at local neighborhood
            neighbors = self._get_spatial_neighbors(events, x, y, radius=3)

            if len(neighbors) >= 8:  # Need sufficient neighbors for corner detection
                # Simple corner criterion: high density in local area
                local_density = len(neighbors) / (np.pi * 3**2)
                if local_density > threshold:
                    corners.append({
                        'x': x,
                        'y': y,
                        'strength': local_density
                    })

        return corners

    def _simple_corner_detection(self, density_map: np.ndarray, threshold: float) -> List[Dict[str, Any]]:
        """Simple corner detection based on local maxima"""
        corners = []

        # Find local maxima in density map
        from scipy.ndimage import maximum_filter
        local_max = (density_map == maximum_filter(density_map, size=3)) & (density_map > threshold)

        y_coords, x_coords = np.where(local_max)

        for y, x in zip(y_coords, x_coords):
            corners.append({
                'x': int(x),
                'y': int(y),
                'strength': float(density_map[y, x])
            })

        return corners

    def _get_spatial_neighbors(self, events: List[Dict[str, Any]], x: float, y: float, radius: float) -> List[Dict[str, Any]]:
        """Get spatial neighbors within radius"""
        neighbors = []
        for event in events:
            ex, ey = event.get('x', 0), event.get('y', 0)
            distance = np.sqrt((ex - x)**2 + (ey - y)**2)
            if distance <= radius and distance > 0:  # Exclude self
                neighbors.append(event)
        return neighbors


class ObjectTracker(AlgorithmModule):
    """
    Object tracking module for event-based vision.

    Tracks objects across time using event data.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR]
        caps.max_latency_ms = 60.0
        caps.real_time_capable = True
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = ["numpy", "scipy"]
        reqs.input_constraints = {"temporal": True, "spatial": True}
        reqs.output_constraints = {"tracks": True, "trajectories": True}
        return reqs

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Track objects using event-based methods.

        Args:
            inputs: Event data with spatial-temporal information

        Returns:
            Object tracks and trajectories
        """
        tracking_method = self.config.get('tracking_method', 'centroid')
        max_tracks = self.config.get('max_tracks', 5)

        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']

            if len(events) < 30:
                return {'tracks': [], 'trajectories': []}

            if tracking_method == 'centroid':
                tracks = self._centroid_tracking(events, max_tracks)
            elif tracking_method == 'kalman':
                tracks = self._kalman_tracking(events, max_tracks)
            else:
                tracks = self._simple_tracking(events, max_tracks)

            return {
                'tracks': tracks,
                'trajectories': [track['trajectory'] for track in tracks],
                'total_tracks': len(tracks),
                'tracking_method': tracking_method
            }

        return inputs

    def _centroid_tracking(self, events: List[Dict[str, Any]], max_tracks: int) -> List[Dict[str, Any]]:
        """Simple centroid-based tracking"""
        # Sort events by time
        sorted_events = sorted(events, key=lambda e: e.get('timestamp', 0))

        # Group into temporal windows
        window_size = 50000000  # 50ms windows
        min_time = sorted_events[0]['timestamp']

        time_windows = []
        current_window = []

        for event in sorted_events:
            window_start = (event['timestamp'] - min_time) // window_size

            if len(time_windows) <= window_start:
                if current_window:
                    time_windows.append(current_window)
                current_window = []

            current_window.append(event)

        if current_window:
            time_windows.append(current_window)

        # Track centroids across windows
        tracks = []

        if len(time_windows) >= 2:
            prev_centroid = self._calculate_centroid(time_windows[0])

            if prev_centroid:
                track = {
                    'track_id': 0,
                    'trajectory': [prev_centroid],
                    'start_time': time_windows[0][0]['timestamp'],
                    'end_time': time_windows[-1][-1]['timestamp']
                }

                for window in time_windows[1:]:
                    centroid = self._calculate_centroid(window)
                    if centroid:
                        track['trajectory'].append(centroid)

                tracks.append(track)

        return tracks

    def _kalman_tracking(self, events: List[Dict[str, Any]], max_tracks: int) -> List[Dict[str, Any]]:
        """Kalman filter-based tracking (simplified)"""
        # Simplified Kalman tracking - in practice would use proper Kalman implementation
        return self._centroid_tracking(events, max_tracks)

    def _simple_tracking(self, events: List[Dict[str, Any]], max_tracks: int) -> List[Dict[str, Any]]:
        """Simple event clustering tracking"""
        tracks = []

        # Group events into spatial-temporal clusters
        clusters = self._cluster_events(events, max_tracks)

        for i, cluster in enumerate(clusters):
            if len(cluster) >= 5:  # Minimum events for a track
                trajectory = []
                timestamps = []

                for event in cluster:
                    trajectory.append((event.get('x', 0), event.get('y', 0)))
                    timestamps.append(event.get('timestamp', 0))

                tracks.append({
                    'track_id': i,
                    'trajectory': trajectory,
                    'start_time': min(timestamps),
                    'end_time': max(timestamps),
                    'event_count': len(cluster)
                })

        return tracks

    def _cluster_events(self, events: List[Dict[str, Any]], max_clusters: int) -> List[List[Dict[str, Any]]]:
        """Simple spatial-temporal clustering of events"""
        if not events:
            return []

        # Sort by time
        sorted_events = sorted(events, key=lambda e: e.get('timestamp', 0))

        clusters = []
        current_cluster = [sorted_events[0]]

        for event in sorted_events[1:]:
            # Check if event belongs to current cluster (spatial proximity)
            cluster_centroid = self._calculate_centroid(current_cluster)
            if cluster_centroid:
                distance = np.sqrt((event.get('x', 0) - cluster_centroid[0])**2 +
                                 (event.get('y', 0) - cluster_centroid[1])**2)

                if distance <= 20:  # Spatial threshold
                    current_cluster.append(event)
                else:
                    # Start new cluster
                    if len(current_cluster) >= 3:
                        clusters.append(current_cluster)
                    current_cluster = [event]

                    if len(clusters) >= max_clusters:
                        break
            else:
                current_cluster.append(event)

        # Add final cluster
        if len(current_cluster) >= 3:
            clusters.append(current_cluster)

        return clusters[:max_clusters]

    def _calculate_centroid(self, events: List[Dict[str, Any]]) -> Tuple[float, float]:
        """Calculate centroid of events"""
        if not events:
            return None

        x_sum = sum(e.get('x', 0) for e in events)
        y_sum = sum(e.get('y', 0) for e in events)

        return (x_sum / len(events), y_sum / len(events))