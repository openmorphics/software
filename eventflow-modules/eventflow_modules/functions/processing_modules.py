"""
Processing and filtering functional modules.

This module provides specialized modules for data processing,
filtering, and transformation operations.
"""

from typing import Any, Dict, List, Union
import numpy as np
from .base import ProcessingModule, TransformModule


class TemporalFilter(ProcessingModule):
    """
    Temporal filtering module for event streams.

    Applies temporal smoothing and filtering operations.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR]
        caps.max_latency_ms = 20.0
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = ["numpy", "scipy"]
        reqs.input_constraints = {"temporal": True}
        reqs.output_constraints = {"temporal": True}
        return reqs

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Apply temporal filtering to event data.

        Args:
            inputs: Event data with timestamps

        Returns:
            Temporally filtered event data
        """
        filter_type = self.config.get('filter_type', 'mean')
        window_size = self.config.get('window_size', 10)

        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']

            if len(events) < window_size:
                return inputs  # Not enough data for filtering

            filtered_events = []

            for i, event in enumerate(events):
                # Get window of events around current event
                start_idx = max(0, i - window_size // 2)
                end_idx = min(len(events), i + window_size // 2 + 1)
                window_events = events[start_idx:end_idx]

                # Apply filtering based on type
                if filter_type == 'mean':
                    filtered_amplitude = np.mean([e.get('amplitude', 0) for e in window_events])
                elif filter_type == 'median':
                    filtered_amplitude = np.median([e.get('amplitude', 0) for e in window_events])
                elif filter_type == 'gaussian':
                    # Simple Gaussian-like weighting
                    weights = np.exp(-np.linspace(-1, 1, len(window_events))**2)
                    weights /= np.sum(weights)
                    amplitudes = [e.get('amplitude', 0) for e in window_events]
                    filtered_amplitude = np.sum(weights * amplitudes)
                else:
                    filtered_amplitude = event.get('amplitude', 0)

                # Create filtered event
                filtered_event = event.copy()
                filtered_event['filtered_amplitude'] = filtered_amplitude
                filtered_event['original_amplitude'] = event.get('amplitude', 0)
                filtered_events.append(filtered_event)

            return {'events': filtered_events, 'filter_applied': filter_type}

        return inputs


class SpatialFilter(ProcessingModule):
    """
    Spatial filtering module for event-based data.

    Applies spatial smoothing and neighborhood operations.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR]
        caps.max_latency_ms = 15.0
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = ["numpy", "scipy"]
        reqs.input_constraints = {"spatial": True}
        reqs.output_constraints = {"spatial": True}
        return reqs

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Apply spatial filtering to event data.

        Args:
            inputs: Event data with spatial coordinates

        Returns:
            Spatially filtered event data
        """
        neighborhood_radius = self.config.get('neighborhood_radius', 5.0)
        filter_type = self.config.get('filter_type', 'density')

        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']
            filtered_events = []

            for event in events:
                x, y = event.get('x', 0), event.get('y', 0)

                # Find neighboring events within radius
                neighbors = []
                for other_event in events:
                    if other_event is event:
                        continue
                    other_x, other_y = other_event.get('x', 0), other_event.get('y', 0)
                    distance = np.sqrt((x - other_x)**2 + (y - other_y)**2)
                    if distance <= neighborhood_radius:
                        neighbors.append(other_event)

                # Apply spatial filtering
                if filter_type == 'density':
                    # Density-based filtering - boost events in dense regions
                    density_factor = len(neighbors) / max(1, len(events) * 0.01)  # Normalize
                    filtered_amplitude = event.get('amplitude', 0) * (1 + density_factor)
                elif filter_type == 'isolation':
                    # Isolation filtering - suppress isolated events
                    isolation_factor = 1.0 / (1 + len(neighbors))
                    filtered_amplitude = event.get('amplitude', 0) * isolation_factor
                else:
                    filtered_amplitude = event.get('amplitude', 0)

                filtered_event = event.copy()
                filtered_event['filtered_amplitude'] = filtered_amplitude
                filtered_event['neighbor_count'] = len(neighbors)
                filtered_events.append(filtered_event)

            return {'events': filtered_events, 'filter_applied': filter_type}

        return inputs


class DataNormalizer(TransformModule):
    """
    Data normalization and scaling module.

    Normalizes event amplitudes and coordinates to standard ranges.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY]
        caps.max_latency_ms = 10.0
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = ["numpy"]
        reqs.input_constraints = {}
        reqs.output_constraints = {"normalized": True}
        return reqs

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Normalize data to standard ranges.

        Args:
            inputs: Raw event data or numerical arrays

        Returns:
            Normalized data
        """
        normalization_type = self.config.get('normalization_type', 'minmax')
        target_range = self.config.get('target_range', [0.0, 1.0])

        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']
            if not events:
                return inputs

            # Extract amplitudes for normalization
            amplitudes = [e.get('amplitude', 0) for e in events]

            if normalization_type == 'minmax':
                min_amp, max_amp = np.min(amplitudes), np.max(amplitudes)
                if max_amp > min_amp:
                    normalized_amplitudes = [
                        target_range[0] + (amp - min_amp) / (max_amp - min_amp) * (target_range[1] - target_range[0])
                        for amp in amplitudes
                    ]
                else:
                    normalized_amplitudes = [target_range[0]] * len(amplitudes)

            elif normalization_type == 'zscore':
                mean_amp, std_amp = np.mean(amplitudes), np.std(amplitudes)
                if std_amp > 0:
                    normalized_amplitudes = [(amp - mean_amp) / std_amp for amp in amplitudes]
                else:
                    normalized_amplitudes = [0.0] * len(amplitudes)

            elif normalization_type == 'robust':
                median_amp = np.median(amplitudes)
                mad_amp = np.median(np.abs(amplitudes - median_amp))
                if mad_amp > 0:
                    normalized_amplitudes = [(amp - median_amp) / mad_amp for amp in amplitudes]
                else:
                    normalized_amplitudes = [0.0] * len(amplitudes)

            else:
                normalized_amplitudes = amplitudes

            # Create normalized events
            normalized_events = []
            for event, norm_amp in zip(events, normalized_amplitudes):
                normalized_event = event.copy()
                normalized_event['normalized_amplitude'] = norm_amp
                normalized_event['original_amplitude'] = event.get('amplitude', 0)
                normalized_events.append(normalized_event)

            return {
                'events': normalized_events,
                'normalization_type': normalization_type,
                'target_range': target_range
            }

        elif hasattr(inputs, '__array__'):
            # Handle numpy arrays
            data = np.asarray(inputs)
            if normalization_type == 'minmax':
                min_val, max_val = np.min(data), np.max(data)
                if max_val > min_val:
                    normalized = target_range[0] + (data - min_val) / (max_val - min_val) * (target_range[1] - target_range[0])
                else:
                    normalized = np.full_like(data, target_range[0])
            else:
                normalized = data  # Return as-is for unsupported types

            return normalized

        return inputs


class FeatureExtractor(TransformModule):
    """
    Feature extraction module for event data.

    Extracts statistical and structural features from event streams.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR]
        caps.output_formats = [self.DataFormat.NUMPY_ARRAY, self.DataFormat.PANDAS_DF]
        caps.max_latency_ms = 50.0
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = ["numpy", "pandas"]
        reqs.input_constraints = {"temporal": True}
        reqs.output_constraints = {"features": True}
        return reqs

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Extract features from event data.

        Args:
            inputs: Event data stream

        Returns:
            Extracted feature vectors
        """
        feature_types = self.config.get('feature_types', ['statistical', 'temporal', 'spatial'])

        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']
            if not events:
                return {'features': np.array([]), 'feature_names': []}

            features = {}
            feature_names = []

            # Statistical features
            if 'statistical' in feature_types:
                amplitudes = [e.get('amplitude', 0) for e in events]
                features.update({
                    'mean_amplitude': np.mean(amplitudes),
                    'std_amplitude': np.std(amplitudes),
                    'min_amplitude': np.min(amplitudes),
                    'max_amplitude': np.max(amplitudes),
                    'median_amplitude': np.median(amplitudes),
                    'event_count': len(events)
                })
                feature_names.extend(['mean_amplitude', 'std_amplitude', 'min_amplitude',
                                    'max_amplitude', 'median_amplitude', 'event_count'])

            # Temporal features
            if 'temporal' in feature_types:
                timestamps = [e.get('timestamp', 0) for e in events]
                if len(timestamps) > 1:
                    time_diffs = np.diff(sorted(timestamps))
                    features.update({
                        'mean_inter_event_time': np.mean(time_diffs),
                        'std_inter_event_time': np.std(time_diffs),
                        'min_inter_event_time': np.min(time_diffs),
                        'max_inter_event_time': np.max(time_diffs),
                        'total_duration': max(timestamps) - min(timestamps)
                    })
                    feature_names.extend(['mean_inter_event_time', 'std_inter_event_time',
                                        'min_inter_event_time', 'max_inter_event_time', 'total_duration'])

            # Spatial features
            if 'spatial' in feature_types:
                x_coords = [e.get('x', 0) for e in events]
                y_coords = [e.get('y', 0) for e in events]
                if x_coords and y_coords:
                    features.update({
                        'mean_x': np.mean(x_coords),
                        'std_x': np.std(x_coords),
                        'mean_y': np.mean(y_coords),
                        'std_y': np.std(y_coords),
                        'spatial_spread': np.sqrt(np.var(x_coords) + np.var(y_coords))
                    })
                    feature_names.extend(['mean_x', 'std_x', 'mean_y', 'std_y', 'spatial_spread'])

            # Convert to numpy array
            feature_vector = np.array([features[name] for name in feature_names])

            return {
                'features': feature_vector,
                'feature_names': feature_names,
                'feature_dict': features
            }

        return inputs