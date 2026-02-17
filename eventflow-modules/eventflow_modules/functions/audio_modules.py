"""
Audio processing functional modules.

This module provides specialized modules for audio processing tasks
including voice activity detection, keyword spotting, and beamforming.
"""

from typing import Any, Dict, List, Union, Tuple
import numpy as np
from .base import AlgorithmModule, ProcessingModule


class VoiceActivityDetector(AlgorithmModule):
    """
    Voice Activity Detection (VAD) module for audio streams.

    Detects presence of speech in audio signals using event-based methods.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR]
        caps.max_latency_ms = 25.0
        caps.real_time_capable = True
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = ["numpy", "scipy"]
        reqs.input_constraints = {"temporal": True, "audio": True}
        reqs.output_constraints = {"speech_segments": True, "vad_decisions": True}
        return reqs

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Detect voice activity in audio event streams.

        Args:
            inputs: Audio event data or signal arrays

        Returns:
            Voice activity detection results
        """
        vad_method = self.config.get('vad_method', 'energy')
        threshold = self.config.get('vad_threshold', 0.3)
        min_duration = self.config.get('min_speech_duration_ms', 100)

        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']

            if len(events) < 10:
                return {'speech_segments': [], 'vad_decisions': []}

            if vad_method == 'energy':
                segments = self._energy_based_vad(events, threshold, min_duration)
            elif vad_method == 'rate':
                segments = self._rate_based_vad(events, threshold, min_duration)
            else:
                segments = self._simple_vad(events, threshold, min_duration)

            return {
                'speech_segments': segments,
                'vad_decisions': [{'timestamp': s['start'], 'decision': True} for s in segments],
                'total_segments': len(segments),
                'vad_method': vad_method
            }

        elif hasattr(inputs, '__array__'):
            # Handle numpy arrays (traditional audio)
            signal = np.asarray(inputs)
            segments = self._signal_energy_vad(signal, threshold, min_duration)

            return {
                'speech_segments': segments,
                'vad_decisions': [{'timestamp': s['start'], 'decision': True} for s in segments],
                'signal_length': len(signal)
            }

        return inputs

    def _energy_based_vad(self, events: List[Dict[str, Any]], threshold: float, min_duration: int) -> List[Dict[str, Any]]:
        """Energy-based VAD using event amplitudes"""
        segments = []

        # Sort events by time
        sorted_events = sorted(events, key=lambda e: e.get('timestamp', 0))

        # Calculate energy in sliding windows
        window_size = 100000000  # 100ms in nanoseconds
        step_size = 50000000    # 50ms step

        current_segment = None
        min_timestamp = sorted_events[0]['timestamp']

        for i in range(0, int((sorted_events[-1]['timestamp'] - min_timestamp) // step_size) + 1):
            window_start = min_timestamp + i * step_size
            window_end = window_start + window_size

            # Get events in current window
            window_events = [e for e in sorted_events if window_start <= e['timestamp'] < window_end]

            if window_events:
                # Calculate average energy
                avg_energy = np.mean([e.get('amplitude', 0) for e in window_events])

                if avg_energy > threshold:
                    if current_segment is None:
                        # Start new segment
                        current_segment = {'start': window_start, 'end': window_end, 'energy': avg_energy}
                    else:
                        # Extend current segment
                        current_segment['end'] = window_end
                        current_segment['energy'] = max(current_segment['energy'], avg_energy)
                else:
                    if current_segment is not None:
                        # End current segment if long enough
                        duration_ms = (current_segment['end'] - current_segment['start']) / 1000000
                        if duration_ms >= min_duration:
                            segments.append(current_segment)
                        current_segment = None

        # Close any open segment
        if current_segment is not None:
            duration_ms = (current_segment['end'] - current_segment['start']) / 1000000
            if duration_ms >= min_duration:
                segments.append(current_segment)

        return segments

    def _rate_based_vad(self, events: List[Dict[str, Any]], threshold: float, min_duration: int) -> List[Dict[str, Any]]:
        """Rate-based VAD using event firing rates"""
        segments = []

        # Sort events by time
        sorted_events = sorted(events, key=lambda e: e.get('timestamp', 0))

        # Calculate firing rate in sliding windows
        window_size = 100000000  # 100ms
        step_size = 50000000    # 50ms

        current_segment = None
        min_timestamp = sorted_events[0]['timestamp']

        for i in range(0, int((sorted_events[-1]['timestamp'] - min_timestamp) // step_size) + 1):
            window_start = min_timestamp + i * step_size
            window_end = window_start + window_size

            # Count events in current window
            event_count = sum(1 for e in sorted_events if window_start <= e['timestamp'] < window_end)
            firing_rate = event_count / (window_size / 1000000000)  # Events per second

            if firing_rate > threshold:
                if current_segment is None:
                    current_segment = {'start': window_start, 'end': window_end, 'rate': firing_rate}
                else:
                    current_segment['end'] = window_end
                    current_segment['rate'] = max(current_segment['rate'], firing_rate)
            else:
                if current_segment is not None:
                    duration_ms = (current_segment['end'] - current_segment['start']) / 1000000
                    if duration_ms >= min_duration:
                        segments.append(current_segment)
                    current_segment = None

        # Close any open segment
        if current_segment is not None:
            duration_ms = (current_segment['end'] - current_segment['start']) / 1000000
            if duration_ms >= min_duration:
                segments.append(current_segment)

        return segments

    def _simple_vad(self, events: List[Dict[str, Any]], threshold: float, min_duration: int) -> List[Dict[str, Any]]:
        """Simple threshold-based VAD"""
        return self._energy_based_vad(events, threshold, min_duration)

    def _signal_energy_vad(self, signal: np.ndarray, threshold: float, min_duration: int) -> List[Dict[str, Any]]:
        """Traditional signal energy-based VAD"""
        segments = []

        # Assuming 16kHz sample rate
        window_samples = int(0.025 * 16000)  # 25ms windows
        step_samples = int(0.010 * 16000)   # 10ms steps

        current_segment = None

        for i in range(0, len(signal) - window_samples, step_samples):
            window = signal[i:i + window_samples]
            energy = np.sum(window ** 2) / len(window)

            if energy > threshold:
                if current_segment is None:
                    current_segment = {'start': i, 'end': i + window_samples, 'energy': energy}
                else:
                    current_segment['end'] = i + window_samples
                    current_segment['energy'] = max(current_segment['energy'], energy)
            else:
                if current_segment is not None:
                    duration_samples = current_segment['end'] - current_segment['start']
                    duration_ms = duration_samples / 16.0  # Assuming 16kHz
                    if duration_ms >= min_duration:
                        segments.append(current_segment)
                    current_segment = None

        return segments


class KeywordSpotter(AlgorithmModule):
    """
    Keyword spotting module for audio event streams.

    Detects specific keywords or phrases in continuous audio.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR]
        caps.max_latency_ms = 100.0
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = ["numpy", "scipy"]
        reqs.input_constraints = {"temporal": True, "audio": True}
        reqs.output_constraints = {"keywords": True, "detections": True}
        return reqs

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Detect keywords in audio event streams.

        Args:
            inputs: Audio event data

        Returns:
            Keyword detection results
        """
        keywords = self.config.get('keywords', ['hello', 'stop'])
        detection_threshold = self.config.get('threshold', 0.7)

        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']

            if len(events) < 50:
                return {'keywords': [], 'detections': []}

            # Simple keyword spotting based on event patterns
            detections = self._pattern_based_kws(events, keywords, detection_threshold)

            return {
                'keywords': keywords,
                'detections': detections,
                'total_detections': len(detections)
            }

        return inputs

    def _pattern_based_kws(self, events: List[Dict[str, Any]], keywords: List[str], threshold: float) -> List[Dict[str, Any]]:
        """Pattern-based keyword spotting"""
        detections = []

        # Sort events by time
        sorted_events = sorted(events, key=lambda e: e.get('timestamp', 0))

        # Look for temporal patterns that might indicate keywords
        # This is a simplified implementation - real KWS would use ML models

        # Group events into potential word segments
        segments = self._segment_audio_events(sorted_events)

        for segment in segments:
            if len(segment) < 10:
                continue

            # Extract features from segment
            features = self._extract_segment_features(segment)

            # Simple pattern matching (in practice, this would be a trained model)
            confidence = self._calculate_pattern_confidence(features, keywords)

            if confidence > threshold:
                detections.append({
                    'keyword': keywords[0],  # Simplified - would determine which keyword
                    'start_time': segment[0]['timestamp'],
                    'end_time': segment[-1]['timestamp'],
                    'confidence': confidence,
                    'segment_length': len(segment)
                })

        return detections

    def _segment_audio_events(self, events: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """Segment audio events into potential word units"""
        segments = []

        if not events:
            return segments

        # Simple segmentation based on silence gaps
        silence_threshold = 50000000  # 50ms in nanoseconds
        current_segment = [events[0]]

        for event in events[1:]:
            time_gap = event['timestamp'] - current_segment[-1]['timestamp']

            if time_gap > silence_threshold:
                # Start new segment
                if len(current_segment) >= 5:  # Minimum segment length
                    segments.append(current_segment)
                current_segment = [event]
            else:
                current_segment.append(event)

        # Add final segment
        if len(current_segment) >= 5:
            segments.append(current_segment)

        return segments

    def _extract_segment_features(self, segment: List[Dict[str, Any]]) -> Dict[str, float]:
        """Extract features from an audio segment"""
        if not segment:
            return {}

        amplitudes = [e.get('amplitude', 0) for e in segment]
        timestamps = [e.get('timestamp', 0) for e in segment]

        features = {
            'duration': timestamps[-1] - timestamps[0] if timestamps else 0,
            'avg_amplitude': np.mean(amplitudes),
            'std_amplitude': np.std(amplitudes),
            'max_amplitude': np.max(amplitudes),
            'event_count': len(segment),
            'avg_inter_event_time': np.mean(np.diff(timestamps)) if len(timestamps) > 1 else 0
        }

        return features

    def _calculate_pattern_confidence(self, features: Dict[str, float], keywords: List[str]) -> float:
        """Calculate confidence that segment matches a keyword pattern"""
        # Simplified confidence calculation
        # In practice, this would use trained models

        duration = features.get('duration', 0) / 1000000000  # Convert to seconds
        event_count = features.get('event_count', 0)
        avg_amplitude = features.get('avg_amplitude', 0)

        # Simple heuristic: keywords typically 0.3-1.0 seconds with moderate-high amplitude
        duration_score = 1.0 if 0.3 <= duration <= 1.0 else 0.5
        amplitude_score = min(1.0, avg_amplitude / 0.8)  # Normalize to expected range
        count_score = min(1.0, event_count / 50)  # Expect reasonable event count

        confidence = (duration_score + amplitude_score + count_score) / 3.0
        return confidence


class AudioBeamformer(ProcessingModule):
    """
    Audio beamforming module for directional signal enhancement.

    Enhances signals from specific directions using event-based methods.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY]
        caps.max_latency_ms = 50.0
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = ["numpy", "scipy"]
        reqs.input_constraints = {"spatial": True, "audio": True}
        reqs.output_constraints = {"beamformed": True}
        return reqs

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Apply beamforming to enhance directional audio signals.

        Args:
            inputs: Multi-channel audio event data

        Returns:
            Beamformed audio output
        """
        beam_angle = self.config.get('beam_angle', 0)  # degrees
        num_channels = self.config.get('num_channels', 4)

        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']

            if len(events) < 20:
                return inputs

            # Apply delay-and-sum beamforming
            beamformed_events = self._delay_sum_beamforming(events, beam_angle, num_channels)

            return {
                'events': beamformed_events,
                'beam_angle': beam_angle,
                'num_channels': num_channels,
                'method': 'delay_and_sum'
            }

        elif hasattr(inputs, '__array__'):
            # Handle traditional multi-channel audio
            signal = np.asarray(inputs)
            if signal.ndim == 2:  # Multi-channel
                beamformed = self._delay_sum_beamforming_signal(signal, beam_angle)
                return beamformed

        return inputs

    def _delay_sum_beamforming(self, events: List[Dict[str, Any]], beam_angle: float, num_channels: int) -> List[Dict[str, Any]]:
        """Delay-and-sum beamforming for event data"""
        beamformed_events = []

        # Group events by time windows
        time_windows = self._temporal_binning_audio(events, window_ms=10)

        for window_events in time_windows:
            if len(window_events) < num_channels:
                continue

            # Simulate multi-channel by assuming events have channel information
            channel_events = {}
            for event in window_events:
                channel = getattr(event, 'channel', event.get('channel', 0)) % num_channels
                if channel not in channel_events:
                    channel_events[channel] = []
                channel_events[channel].append(event)

            # Apply beamforming weights
            beamformed_amplitude = 0
            weight_sum = 0

            for channel in range(num_channels):
                if channel in channel_events:
                    channel_avg_amp = np.mean([e.get('amplitude', 0) for e in channel_events[channel]])

                    # Calculate delay based on beam angle (simplified)
                    delay_samples = int(channel * np.sin(np.radians(beam_angle)) * 10)  # Simplified delay

                    # Apply delay and sum
                    weight = np.exp(-1j * 2 * np.pi * delay_samples / 100)  # Simplified phase shift
                    beamformed_amplitude += channel_avg_amp * abs(weight)
                    weight_sum += abs(weight)

            if weight_sum > 0:
                beamformed_amplitude /= weight_sum

                # Create beamformed event
                beamformed_event = {
                    'timestamp': window_events[0]['timestamp'],
                    'amplitude': beamformed_amplitude,
                    'beam_angle': beam_angle,
                    'method': 'delay_and_sum'
                }
                beamformed_events.append(beamformed_event)

        return beamformed_events

    def _delay_sum_beamforming_signal(self, signal: np.ndarray, beam_angle: float) -> np.ndarray:
        """Traditional delay-and-sum beamforming for signal arrays"""
        if signal.shape[0] < 4:  # Need at least 4 channels
            return signal[0] if signal.shape[0] > 0 else signal

        num_channels, num_samples = signal.shape

        # Simplified delay calculation (assuming linear array)
        delays = np.arange(num_channels) * np.sin(np.radians(beam_angle)) * 0.1  # 0.1 sample delay per channel

        # Apply delays and sum
        beamformed = np.zeros(num_samples)

        for channel in range(num_channels):
            delay_samples = int(delays[channel])
            if delay_samples >= 0:
                beamformed[:num_samples-delay_samples] += signal[channel, delay_samples:]
            else:
                beamformed[-delay_samples:] += signal[channel, :num_samples+delay_samples]

        # Normalize
        beamformed /= num_channels

        return beamformed

    def _temporal_binning_audio(self, events: List[Dict[str, Any]], window_ms: int) -> List[List[Dict[str, Any]]]:
        """Group audio events into temporal windows"""
        if not events:
            return []

        window_ns = window_ms * 1000000

        # Sort by time
        sorted_events = sorted(events, key=lambda e: e.get('timestamp', 0))
        min_time = sorted_events[0]['timestamp']

        windows = []
        current_window = []
        current_window_start = min_time

        for event in sorted_events:
            if event['timestamp'] >= current_window_start + window_ns:
                if current_window:
                    windows.append(current_window)
                current_window = [event]
                current_window_start = event['timestamp']
            else:
                current_window.append(event)

        if current_window:
            windows.append(current_window)

        return windows