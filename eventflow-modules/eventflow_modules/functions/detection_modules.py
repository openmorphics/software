"""
Detection and classification functional modules.

This module provides specialized modules for anomaly detection,
pattern recognition, and classification tasks.
"""

from typing import Any, Dict, List, Union
import numpy as np
from .base import AlgorithmModule


class AnomalyDetector(AlgorithmModule):
    """
    Anomaly detection module using statistical methods.

    Detects outliers and unusual patterns in event streams.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR]
        caps.max_latency_ms = 30.0
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = ["numpy", "scipy"]
        reqs.input_constraints = {"temporal": True, "numerical": True}
        reqs.output_constraints = {"anomaly_scores": True}
        return reqs

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Detect anomalies using statistical methods.

        Args:
            inputs: Event data or numerical arrays

        Returns:
            Anomalies with confidence scores
        """
        threshold = self.config.get('threshold', 2.0)
        window_size = self.config.get('window_size', 100)

        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']
            # Simple anomaly detection based on amplitude
            if events:
                amplitudes = [e.get('amplitude', 0) for e in events]
                mean_amp = np.mean(amplitudes)
                std_amp = np.std(amplitudes)

                anomalies = []
                for event in events:
                    amp = event.get('amplitude', 0)
                    z_score = abs(amp - mean_amp) / (std_amp + 1e-6)
                    if z_score > threshold:
                        anomalies.append({
                            **event,
                            'anomaly_score': z_score,
                            'is_anomaly': True
                        })

                return {
                    'anomalies': anomalies,
                    'total_events': len(events),
                    'anomaly_rate': len(anomalies) / len(events) if events else 0
                }

        return inputs


class PatternClassifier(AlgorithmModule):
    """
    Pattern classification module using simple feature extraction.

    Classifies patterns in event streams based on temporal features.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR]
        caps.max_latency_ms = 40.0
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = ["numpy", "scipy"]
        reqs.input_constraints = {"temporal": True, "spatial": True}
        reqs.output_constraints = {"classification": True, "confidence": True}
        return reqs

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Classify patterns in event data.

        Args:
            inputs: Event data with spatial-temporal patterns

        Returns:
            Classified patterns with confidence scores
        """
        # Simple classification based on event density and distribution
        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']

            if len(events) < 10:
                return {'classification': 'insufficient_data', 'confidence': 0.0}

            # Extract simple features
            x_coords = [e.get('x', 0) for e in events]
            y_coords = [e.get('y', 0) for e in events]
            timestamps = [e.get('timestamp', 0) for e in events]

            # Calculate spatial spread
            x_spread = np.std(x_coords) if x_coords else 0
            y_spread = np.std(y_coords) if y_coords else 0

            # Calculate temporal density
            time_span = max(timestamps) - min(timestamps) if timestamps else 1
            density = len(events) / (time_span + 1)

            # Simple classification logic
            if density > 10 and (x_spread > 5 or y_spread > 5):
                classification = 'high_activity_spread'
                confidence = 0.8
            elif density > 5:
                classification = 'moderate_activity'
                confidence = 0.6
            else:
                classification = 'low_activity'
                confidence = 0.4

            return {
                'classification': classification,
                'confidence': confidence,
                'features': {
                    'event_count': len(events),
                    'spatial_spread_x': x_spread,
                    'spatial_spread_y': y_spread,
                    'temporal_density': density
                }
            }

        return inputs


class MotionDetector(AlgorithmModule):
    """
    Motion detection module for event-based cameras.

    Detects moving objects and tracks their trajectories.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR]
        caps.max_latency_ms = 25.0
        caps.real_time_capable = True
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = ["numpy"]
        reqs.input_constraints = {"temporal": True, "spatial": True}
        reqs.output_constraints = {"motion_vectors": True}
        return reqs

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Detect motion patterns in event streams.

        Args:
            inputs: Event data from event-based sensors

        Returns:
            Motion vectors and trajectories
        """
        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']

            if len(events) < 20:
                return {'motion_detected': False, 'motion_vectors': []}

            # Group events by time windows
            time_windows = {}
            window_size = 1000000  # 1ms in nanoseconds

            for event in events:
                timestamp = event.get('timestamp', 0)
                window = timestamp // window_size
                if window not in time_windows:
                    time_windows[window] = []
                time_windows[window].append(event)

            # Calculate motion vectors between consecutive windows
            motion_vectors = []
            windows = sorted(time_windows.keys())

            for i in range(1, len(windows)):
                current_events = time_windows[windows[i]]
                prev_events = time_windows[windows[i-1]]

                if current_events and prev_events:
                    # Calculate centroid movement
                    current_centroid = self._calculate_centroid(current_events)
                    prev_centroid = self._calculate_centroid(prev_events)

                    if current_centroid and prev_centroid:
                        motion_vector = {
                            'dx': current_centroid[0] - prev_centroid[0],
                            'dy': current_centroid[1] - prev_centroid[1],
                            'magnitude': np.sqrt(
                                (current_centroid[0] - prev_centroid[0])**2 +
                                (current_centroid[1] - prev_centroid[1])**2
                            ),
                            'timestamp': windows[i] * window_size
                        }
                        motion_vectors.append(motion_vector)

            return {
                'motion_detected': len(motion_vectors) > 0,
                'motion_vectors': motion_vectors,
                'total_windows': len(windows)
            }

        return inputs

    def _calculate_centroid(self, events: List[Dict[str, Any]]) -> tuple:
        """Calculate centroid of events"""
        if not events:
            return None

        x_sum = sum(e.get('x', 0) for e in events)
        y_sum = sum(e.get('y', 0) for e in events)

        return (x_sum / len(events), y_sum / len(events))