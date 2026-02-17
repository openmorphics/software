"""
Generic functional modules for data flow control and system utilities.

This module provides non-domain-specific functional components that can be
used across different applications for routing, buffering, monitoring, and
orchestration of event-driven pipelines.
"""

from typing import Any, Dict, List, Union, Optional, Callable
import time
from collections import deque
from .base import TransformModule, ControlModule


class EventBuffer(TransformModule):
    """
    Event buffering module for temporal smoothing and rate control.

    Buffers events in time windows or by count, providing controlled
    data flow and temporal aggregation capabilities.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY, self.DataFormat.CUSTOM]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY, self.DataFormat.CUSTOM]
        caps.max_latency_ms = 5.0
        caps.real_time_capable = True
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = []
        reqs.input_constraints = {}
        reqs.output_constraints = {"buffered": True}
        return reqs

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.buffer_type = config.get('buffer_type', 'temporal')  # 'temporal', 'count', 'size'
        self.buffer_size = config.get('buffer_size', 100)
        self.flush_interval_ms = config.get('flush_interval_ms', 100.0)
        self.auto_flush = config.get('auto_flush', True)

        # Initialize buffer based on type
        if self.buffer_type == 'temporal':
            self.buffer = {}  # timestamp -> events
            self.last_flush_time = time.time() * 1000  # milliseconds
        else:
            self.buffer = deque(maxlen=self.buffer_size if self.buffer_type == 'count' else None)

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Buffer and optionally flush events based on configured strategy.

        Args:
            inputs: Events or data to buffer

        Returns:
            Buffered data or flushed buffer contents
        """
        current_time = time.time() * 1000

        if self.buffer_type == 'temporal':
            return self._process_temporal_buffer(inputs, current_time)
        elif self.buffer_type == 'count':
            return self._process_count_buffer(inputs)
        elif self.buffer_type == 'size':
            return self._process_size_buffer(inputs)
        else:
            return inputs

    def _process_temporal_buffer(self, inputs: Union[Any, Dict[str, Any]], current_time: float) -> Union[Any, Dict[str, Any]]:
        """Process temporal buffering with time-based windows"""
        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']

            # Add events to time-based buffer
            for event in events:
                timestamp = event.get('timestamp', current_time)
                time_key = int(timestamp // self.flush_interval_ms) * self.flush_interval_ms

                if time_key not in self.buffer:
                    self.buffer[time_key] = []
                self.buffer[time_key].append(event)

            # Check for auto-flush
            if self.auto_flush and (current_time - self.last_flush_time) >= self.flush_interval_ms:
                flushed_data = self._flush_temporal_buffer(current_time)
                if flushed_data:
                    self.last_flush_time = current_time
                    return flushed_data

        return {'buffered_events': sum(len(events) for events in self.buffer.values())}

    def _process_count_buffer(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """Process count-based buffering"""
        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']

            # Add events to buffer
            for event in events:
                self.buffer.append(event)

            # Auto-flush when buffer is full
            if self.auto_flush and len(self.buffer) >= self.buffer_size:
                return {'events': list(self.buffer), 'buffer_flushed': True, 'buffer_size': len(self.buffer)}
            else:
                return {'buffered_count': len(self.buffer), 'buffer_capacity': self.buffer_size}

        return inputs

    def _process_size_buffer(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """Process size-based buffering (simplified)"""
        # Size-based buffering would track memory usage
        # For now, delegate to count-based
        return self._process_count_buffer(inputs)

    def _flush_temporal_buffer(self, current_time: float) -> Optional[Dict[str, Any]]:
        """Flush expired temporal buffers"""
        flush_threshold = current_time - (self.flush_interval_ms * 2)  # Allow some hysteresis

        expired_keys = [k for k in self.buffer.keys() if k < flush_threshold]

        if expired_keys:
            flushed_events = []
            for key in expired_keys:
                flushed_events.extend(self.buffer.pop(key))

            return {
                'events': flushed_events,
                'flushed_windows': len(expired_keys),
                'total_events': len(flushed_events)
            }

        return None

    def flush(self) -> Dict[str, Any]:
        """Manually flush all buffered data"""
        if self.buffer_type == 'temporal':
            all_events = []
            for events in self.buffer.values():
                all_events.extend(events)
            flushed_count = len(self.buffer)
            self.buffer.clear()
            return {'events': all_events, 'flushed_windows': flushed_count}
        else:
            events = list(self.buffer)
            self.buffer.clear()
            return {'events': events, 'buffer_flushed': True}


class EventRouter(TransformModule):
    """
    Event routing module for conditional data flow control.

    Routes events to different outputs based on configurable criteria,
    enabling complex pipeline branching and conditional processing.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY, self.DataFormat.CUSTOM]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.CUSTOM]
        caps.max_latency_ms = 2.0
        caps.real_time_capable = True
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = []
        reqs.input_constraints = {}
        reqs.output_constraints = {"routed": True}
        return reqs

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.routing_rules = config.get('routing_rules', [])
        self.default_route = config.get('default_route', 'output')
        self.route_stats = {}

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Route events based on configured rules.

        Args:
            inputs: Events to route

        Returns:
            Routed event outputs
        """
        outputs = {}

        if isinstance(inputs, dict) and 'events' in inputs:
            events = inputs['events']

            # Initialize route collections
            for rule in self.routing_rules:
                route_name = rule.get('route', 'output')
                if route_name not in outputs:
                    outputs[route_name] = []

            # Default route
            if self.default_route not in outputs:
                outputs[self.default_route] = []

            # Route each event
            for event in events:
                route = self._determine_route(event)
                outputs[route].append(event)

                # Update statistics
                if route not in self.route_stats:
                    self.route_stats[route] = 0
                self.route_stats[route] += 1

        # Add routing statistics
        outputs['_routing_stats'] = dict(self.route_stats)

        return outputs

    def _determine_route(self, event: Dict[str, Any]) -> str:
        """Determine which route an event should take"""
        for rule in self.routing_rules:
            if self._matches_rule(event, rule):
                return rule.get('route', 'output')

        return self.default_route

    def _matches_rule(self, event: Dict[str, Any], rule: Dict[str, Any]) -> bool:
        """Check if event matches a routing rule"""
        condition = rule.get('condition', {})

        for key, criteria in condition.items():
            if key not in event:
                return False

            event_value = event[key]

            if isinstance(criteria, dict):
                # Range or comparison criteria
                if 'min' in criteria and event_value < criteria['min']:
                    return False
                if 'max' in criteria and event_value > criteria['max']:
                    return False
                if 'equals' in criteria and event_value != criteria['equals']:
                    return False
                if 'not_equals' in criteria and event_value == criteria['not_equals']:
                    return False
            else:
                # Direct equality check
                if event_value != criteria:
                    return False

        return True

    def add_routing_rule(self, rule: Dict[str, Any]) -> None:
        """Add a new routing rule dynamically"""
        self.routing_rules.append(rule)
        self.logger.info(f"Added routing rule: {rule}")

    def clear_routing_stats(self) -> None:
        """Clear routing statistics"""
        self.route_stats.clear()


class EventMultiplexer(TransformModule):
    """
    Event multiplexing module for combining multiple data streams.

    Combines events from multiple sources into a single stream,
    with optional synchronization and ordering.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.CUSTOM]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR]
        caps.max_latency_ms = 5.0
        caps.real_time_capable = True
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = []
        reqs.input_constraints = {"multiple_streams": True}
        reqs.output_constraints = {"multiplexed": True}
        return reqs

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.sync_mode = config.get('sync_mode', 'none')  # 'none', 'time', 'sequence'
        self.max_latency_ms = config.get('max_latency_ms', 100.0)
        self.stream_buffers = {}

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Multiplex multiple event streams into one.

        Args:
            inputs: Dictionary of named event streams

        Returns:
            Combined event stream
        """
        if not isinstance(inputs, dict):
            return inputs

        combined_events = []
        stream_info = {}

        # Process each input stream
        for stream_name, stream_data in inputs.items():
            if isinstance(stream_data, dict) and 'events' in stream_data:
                events = stream_data['events']
                stream_info[stream_name] = len(events)

                # Add stream identifier to events
                for event in events:
                    event_copy = event.copy()
                    event_copy['_stream_source'] = stream_name
                    combined_events.append(event_copy)

        # Apply synchronization if configured
        if self.sync_mode == 'time':
            combined_events = self._sync_by_time(combined_events)
        elif self.sync_mode == 'sequence':
            combined_events = self._sync_by_sequence(combined_events)

        return {
            'events': combined_events,
            'total_events': len(combined_events),
            'stream_info': stream_info,
            'sync_mode': self.sync_mode
        }

    def _sync_by_time(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Synchronize events by timestamp"""
        return sorted(events, key=lambda e: e.get('timestamp', 0))

    def _sync_by_sequence(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Synchronize events by sequence number if available"""
        # Look for sequence numbers, fall back to time
        if any('sequence' in event for event in events):
            return sorted(events, key=lambda e: e.get('sequence', e.get('timestamp', 0)))
        else:
            return self._sync_by_time(events)


class PerformanceMonitor(TransformModule):
    """
    Performance monitoring module for pipeline telemetry.

    Monitors latency, throughput, and resource usage across the pipeline,
    providing real-time performance metrics and health monitoring.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY, self.DataFormat.CUSTOM]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY, self.DataFormat.CUSTOM]
        caps.max_latency_ms = 1.0
        caps.real_time_capable = True
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = []
        reqs.input_constraints = {}
        reqs.output_constraints = {"monitored": True}
        return reqs

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.monitor_metrics = config.get('metrics', ['latency', 'throughput', 'count'])
        self.report_interval_ms = config.get('report_interval_ms', 1000.0)
        self.stats_window_size = config.get('stats_window_size', 100)

        # Performance tracking
        self.start_time = time.time() * 1000
        self.event_count = 0
        self.latency_samples = deque(maxlen=self.stats_window_size)
        self.throughput_samples = deque(maxlen=self.stats_window_size)
        self.last_report_time = self.start_time

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Monitor performance and add telemetry to data stream.

        Args:
            inputs: Data to monitor and pass through

        Returns:
            Data with performance metrics attached
        """
        current_time = time.time() * 1000
        processing_start = time.time() * 1000

        # Count events
        event_count = self._count_events(inputs)
        self.event_count += event_count

        # Calculate latency (simplified)
        latency = time.time() * 1000 - processing_start
        self.latency_samples.append(latency)

        # Calculate throughput
        time_elapsed = current_time - self.start_time
        if time_elapsed > 0:
            throughput = (self.event_count / time_elapsed) * 1000  # events per second
            self.throughput_samples.append(throughput)

        # Prepare output with monitoring data
        output = inputs.copy() if isinstance(inputs, dict) else {'original_data': inputs}

        # Add performance metrics
        if 'latency' in self.monitor_metrics:
            output['_performance_latency_ms'] = latency
            output['_performance_latency_avg_ms'] = sum(self.latency_samples) / len(self.latency_samples) if self.latency_samples else 0

        if 'throughput' in self.monitor_metrics:
            output['_performance_throughput_eps'] = throughput if self.throughput_samples else 0

        if 'count' in self.monitor_metrics:
            output['_performance_event_count'] = self.event_count
            output['_performance_batch_size'] = event_count

        # Periodic detailed report
        if (current_time - self.last_report_time) >= self.report_interval_ms:
            report = self._generate_performance_report(current_time)
            output['_performance_report'] = report
            self.last_report_time = current_time

        return output

    def _count_events(self, inputs: Union[Any, Dict[str, Any]]) -> int:
        """Count events in input data"""
        if isinstance(inputs, dict):
            if 'events' in inputs:
                events = inputs['events']
                return len(events) if isinstance(events, list) else 1
            elif 'total_events' in inputs:
                return inputs['total_events']
        return 1

    def _generate_performance_report(self, current_time: float) -> Dict[str, Any]:
        """Generate detailed performance report"""
        time_elapsed = current_time - self.start_time

        return {
            'timestamp': current_time,
            'uptime_ms': time_elapsed,
            'total_events': self.event_count,
            'avg_throughput_eps': sum(self.throughput_samples) / len(self.throughput_samples) if self.throughput_samples else 0,
            'avg_latency_ms': sum(self.latency_samples) / len(self.latency_samples) if self.latency_samples else 0,
            'max_latency_ms': max(self.latency_samples) if self.latency_samples else 0,
            'min_latency_ms': min(self.latency_samples) if self.latency_samples else 0,
            'metrics_enabled': self.monitor_metrics
        }

    def reset_stats(self) -> None:
        """Reset performance statistics"""
        self.start_time = time.time() * 1000
        self.event_count = 0
        self.latency_samples.clear()
        self.throughput_samples.clear()
        self.last_report_time = self.start_time
        self.logger.info("Performance statistics reset")


class ConditionalProcessor(ControlModule):
    """
    Conditional processing module for pipeline branching.

    Processes data only when certain conditions are met,
    enabling conditional execution in event-driven pipelines.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY, self.DataFormat.CUSTOM]
        caps.output_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY, self.DataFormat.CUSTOM]
        caps.max_latency_ms = 3.0
        caps.real_time_capable = True
        return caps

    def _declare_requirements(self):
        reqs = super()._declare_requirements()
        reqs.dependencies = []
        reqs.input_constraints = {}
        reqs.output_constraints = {"conditionally_processed": True}
        return reqs

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.conditions = config.get('conditions', [])
        self.true_action = config.get('true_action', 'pass')  # 'pass', 'block', 'modify'
        self.false_action = config.get('false_action', 'pass')  # 'pass', 'block', 'modify'
        self.condition_stats = {'true': 0, 'false': 0}

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Process data conditionally based on configured criteria.

        Args:
            inputs: Data to conditionally process

        Returns:
            Processed or unmodified data based on conditions
        """
        condition_met = self._evaluate_conditions(inputs)

        # Update statistics
        self.condition_stats['true' if condition_met else 'false'] += 1

        if condition_met:
            if self.true_action == 'pass':
                return self._add_condition_metadata(inputs, True)
            elif self.true_action == 'block':
                return {'blocked': True, 'reason': 'condition_met', 'condition_stats': self.condition_stats}
            elif self.true_action == 'modify':
                return self._modify_data(inputs, True)
        else:
            if self.false_action == 'pass':
                return self._add_condition_metadata(inputs, False)
            elif self.false_action == 'block':
                return {'blocked': True, 'reason': 'condition_not_met', 'condition_stats': self.condition_stats}
            elif self.false_action == 'modify':
                return self._modify_data(inputs, False)

        return inputs

    def _evaluate_conditions(self, inputs: Union[Any, Dict[str, Any]]) -> bool:
        """Evaluate all configured conditions"""
        if not self.conditions:
            return True  # No conditions means always true

        for condition in self.conditions:
            if not self._check_single_condition(inputs, condition):
                return False

        return True

    def _check_single_condition(self, inputs: Union[Any, Dict[str, Any]], condition: Dict[str, Any]) -> bool:
        """Check a single condition against input data"""
        field = condition.get('field')
        operator = condition.get('operator', 'equals')
        value = condition.get('value')

        if not field or not isinstance(inputs, dict):
            return False

        actual_value = self._get_nested_value(inputs, field.split('.'))
        if actual_value is None:
            return False

        if operator == 'equals':
            return actual_value == value
        elif operator == 'not_equals':
            return actual_value != value
        elif operator == 'greater':
            return actual_value > value
        elif operator == 'less':
            return actual_value < value
        elif operator == 'greater_equal':
            return actual_value >= value
        elif operator == 'less_equal':
            return actual_value <= value
        elif operator == 'contains':
            return value in actual_value if isinstance(actual_value, (list, str)) else False
        elif operator == 'not_contains':
            return value not in actual_value if isinstance(actual_value, (list, str)) else True

        return False

    def _get_nested_value(self, data: Dict[str, Any], keys: List[str]) -> Any:
        """Get nested value from dictionary using dot notation"""
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def _add_condition_metadata(self, inputs: Union[Any, Dict[str, Any]], condition_result: bool) -> Union[Any, Dict[str, Any]]:
        """Add condition evaluation metadata to output"""
        if isinstance(inputs, dict):
            result = inputs.copy()
            result['_condition_met'] = condition_result
            result['_condition_stats'] = self.condition_stats.copy()
            return result
        else:
            return {
                'original_data': inputs,
                '_condition_met': condition_result,
                '_condition_stats': self.condition_stats.copy()
            }

    def _modify_data(self, inputs: Union[Any, Dict[str, Any]], condition_result: bool) -> Union[Any, Dict[str, Any]]:
        """Modify data based on condition result"""
        if isinstance(inputs, dict):
            result = inputs.copy()
            result['_condition_met'] = condition_result
            result['_processed_by_condition'] = True

            # Add conditional processing marker
            if condition_result:
                result['_condition_action'] = 'true_branch_processed'
            else:
                result['_condition_action'] = 'false_branch_processed'

            return result

        return inputs

    def add_condition(self, condition: Dict[str, Any]) -> None:
        """Add a new condition dynamically"""
        self.conditions.append(condition)
        self.logger.info(f"Added condition: {condition}")

    def clear_stats(self) -> None:
        """Clear condition evaluation statistics"""
        self.condition_stats = {'true': 0, 'false': 0}


class StateManager(TransformModule):
    """
    Manages persistent state across processing cycles.

    Provides thread-safe state storage, retrieval, and lifecycle management
    for modules that need to maintain context between processing calls.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._state_store = {}
        self._state_lock = None  # Would use threading.Lock in real implementation

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY, self.DataFormat.PANDAS_DF]
        caps.output_formats = caps.input_formats
        caps.max_latency_ms = 2.0
        caps.real_time_capable = True
        return caps

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Process inputs with state management.

        Args:
            inputs: Input data to process

        Returns:
            Processed data with state context
        """
        operation = self.config.get('operation', 'get')
        state_key = self.config.get('state_key', 'default')

        if operation == 'set':
            value = inputs.get('value', inputs)
            self._set_state(state_key, value)
            return {**inputs, 'state_updated': True}

        elif operation == 'get':
            state_value = self._get_state(state_key)
            return {**inputs, 'state': state_value}

        elif operation == 'update':
            current_state = self._get_state(state_key, {})
            updates = inputs.get('updates', {})
            new_state = {**current_state, **updates}
            self._set_state(state_key, new_state)
            return {**inputs, 'state': new_state, 'updated': True}

        elif operation == 'clear':
            self._clear_state(state_key)
            return {**inputs, 'state_cleared': True}

        return inputs

    def _set_state(self, key: str, value: Any):
        """Set state value for key."""
        # Thread-safe implementation would use lock
        self._state_store[key] = value

    def _get_state(self, key: str, default=None):
        """Get state value for key."""
        return self._state_store.get(key, default)

    def _clear_state(self, key: str):
        """Clear state for key."""
        self._state_store.pop(key, None)


class DataValidator(TransformModule):
    """
    Validates input/output data against schemas and constraints.

    Ensures data quality and compatibility by validating structure,
    types, and value ranges before and after processing.
    """

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY, self.DataFormat.PANDAS_DF]
        caps.output_formats = caps.input_formats
        caps.max_latency_ms = 3.0
        caps.real_time_capable = True
        return caps

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Validate input data and annotate with validation results.

        Args:
            inputs: Input data to validate

        Returns:
            Data with validation annotations
        """
        validation_rules = self.config.get('validation_rules', [])
        strict_mode = self.config.get('strict_mode', False)

        validation_results = []
        is_valid = True

        for rule in validation_rules:
            rule_type = rule.get('type', 'schema')
            rule_name = rule.get('name', 'unnamed_rule')

            if rule_type == 'schema':
                result = self._validate_schema(inputs, rule)
            elif rule_type == 'range':
                result = self._validate_range(inputs, rule)
            elif rule_type == 'type':
                result = self._validate_type(inputs, rule)
            else:
                result = {'valid': True, 'message': f'Unknown rule type: {rule_type}'}

            validation_results.append({
                'rule': rule_name,
                'valid': result.get('valid', True),
                'message': result.get('message', '')
            })

            if not result.get('valid', True):
                is_valid = False

        # Handle validation failure
        if not is_valid and strict_mode:
            raise ValueError(f"Data validation failed: {validation_results}")

        return {
            **inputs,
            'validation': {
                'passed': is_valid,
                'results': validation_results,
                'timestamp': time.time()
            }
        }

    def _validate_schema(self, data: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against schema requirements."""
        required_fields = rule.get('required_fields', [])
        field_types = rule.get('field_types', {})

        for field in required_fields:
            if field not in data:
                return {'valid': False, 'message': f'Missing required field: {field}'}

        for field, expected_type in field_types.items():
            if field in data:
                actual_value = data[field]
                if not isinstance(actual_value, expected_type):
                    return {'valid': False, 'message': f'Field {field} has wrong type: expected {expected_type.__name__}'}

        return {'valid': True, 'message': 'Schema validation passed'}

    def _validate_range(self, data: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Validate numeric ranges."""
        field = rule.get('field')
        min_val = rule.get('min')
        max_val = rule.get('max')

        if field not in data:
            return {'valid': False, 'message': f'Field {field} not found for range validation'}

        value = data[field]
        if not isinstance(value, (int, float)):
            return {'valid': False, 'message': f'Field {field} is not numeric'}

        if min_val is not None and value < min_val:
            return {'valid': False, 'message': f'Field {field} below minimum: {value} < {min_val}'}

        if max_val is not None and value > max_val:
            return {'valid': False, 'message': f'Field {field} above maximum: {value} > {max_val}'}

        return {'valid': True, 'message': 'Range validation passed'}

    def _validate_type(self, data: Dict[str, Any], rule: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data types."""
        field = rule.get('field')
        expected_type = rule.get('expected_type')

        if field not in data:
            return {'valid': False, 'message': f'Field {field} not found for type validation'}

        actual_type = type(data[field])
        if actual_type != expected_type:
            return {'valid': False, 'message': f'Field {field} has wrong type: {actual_type.__name__} != {expected_type.__name__}'}

        return {'valid': True, 'message': 'Type validation passed'}


class EventLogger(TransformModule):
    """
    Structured event logging and audit trail generation.

    Captures processing events, decisions, and metrics for debugging,
    monitoring, and compliance purposes.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._log_buffer = []
        self._log_level = config.get('log_level', 'INFO')

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY, self.DataFormat.PANDAS_DF]
        caps.output_formats = caps.input_formats
        caps.max_latency_ms = 1.0
        caps.real_time_capable = True
        return caps

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Process inputs and generate audit logs.

        Args:
            inputs: Input data to log and process

        Returns:
            Data with logging annotations
        """
        log_events = self.config.get('log_events', ['processing_start', 'processing_end'])
        include_metrics = self.config.get('include_metrics', True)

        # Create log entry
        log_entry = {
            'timestamp': time.time(),
            'module': self.config.get('name', 'unknown'),
            'input_type': type(inputs).__name__,
            'events': []
        }

        if 'processing_start' in log_events:
            log_entry['events'].append({
                'event': 'processing_start',
                'data_summary': self._summarize_data(inputs)
            })

        if include_metrics:
            log_entry['metrics'] = self._extract_metrics(inputs)

        # Log the entry
        self._log_entry(log_entry)

        # Process the data (pass through)
        result = inputs

        if 'processing_end' in log_events:
            end_entry = {
                'timestamp': time.time(),
                'event': 'processing_end',
                'output_summary': self._summarize_data(result)
            }
            self._log_entry(end_entry)

        # Attach log reference to output
        if isinstance(result, dict):
            result = {**result, 'log_reference': log_entry.get('log_id')}

        return result

    def _summarize_data(self, data: Any) -> Dict[str, Any]:
        """Create a summary of data for logging."""
        if isinstance(data, dict):
            return {
                'type': 'dict',
                'keys': list(data.keys()),
                'size': len(data)
            }
        elif isinstance(data, list):
            return {
                'type': 'list',
                'length': len(data),
                'element_types': list(set(type(x).__name__ for x in data[:5]))  # Sample first 5
            }
        else:
            return {
                'type': type(data).__name__,
                'repr': str(data)[:100]  # Truncate long representations
            }

    def _extract_metrics(self, data: Any) -> Dict[str, Any]:
        """Extract relevant metrics from data."""
        metrics = {}

        if isinstance(data, dict):
            # Count events if present
            if 'events' in data and isinstance(data['events'], list):
                metrics['event_count'] = len(data['events'])

            # Extract numeric metadata
            if 'metadata' in data and isinstance(data['metadata'], dict):
                for key, value in data['metadata'].items():
                    if isinstance(value, (int, float)):
                        metrics[f'metadata_{key}'] = value

        return metrics

    def _log_entry(self, entry: Dict[str, Any]):
        """Log an entry (could be to file, database, etc.)."""
        # In a real implementation, this would write to a logging system
        self._log_buffer.append(entry)

        # Simple console logging for demonstration
        if self._log_level == 'DEBUG':
            print(f"[LOG] {entry}")


class LoadBalancer(TransformModule):
    """
    Distributes processing load across multiple instances or workers.

    Implements load balancing strategies for horizontal scaling and
    resource optimization in distributed processing pipelines.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._worker_states = {}
        self._strategy = config.get('strategy', 'round_robin')

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY, self.DataFormat.PANDAS_DF]
        caps.output_formats = caps.input_formats
        caps.max_latency_ms = 5.0
        caps.real_time_capable = True
        return caps

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Route input to appropriate worker based on load balancing strategy.

        Args:
            inputs: Input data to route

        Returns:
            Data routed to worker with routing metadata
        """
        workers = self.config.get('workers', ['worker_1', 'worker_2', 'worker_3'])
        strategy = self.config.get('strategy', 'round_robin')

        # Select worker based on strategy
        selected_worker = self._select_worker(workers, inputs, strategy)

        # Update worker state
        self._update_worker_load(selected_worker, inputs)

        # Add routing metadata
        routing_info = {
            'selected_worker': selected_worker,
            'strategy': strategy,
            'timestamp': time.time(),
            'load_distribution': self._get_load_distribution(workers)
        }

        if isinstance(inputs, dict):
            return {**inputs, 'routing': routing_info}
        else:
            return {'data': inputs, 'routing': routing_info}

    def _select_worker(self, workers: List[str], inputs: Any, strategy: str) -> str:
        """Select a worker based on the load balancing strategy."""
        if strategy == 'round_robin':
            # Simple round-robin selection
            current_index = getattr(self, '_rr_index', 0)
            selected = workers[current_index % len(workers)]
            self._rr_index = current_index + 1
            return selected

        elif strategy == 'least_loaded':
            # Select worker with lowest load
            loads = {worker: self._worker_states.get(worker, {}).get('load', 0) for worker in workers}
            return min(loads, key=loads.get)

        elif strategy == 'random':
            # Random selection
            import random
            return random.choice(workers)

        elif strategy == 'hash':
            # Hash-based selection for consistency
            hash_key = self._get_hash_key(inputs)
            return workers[hash(hash_key) % len(workers)]

        else:
            return workers[0]  # Default to first worker

    def _update_worker_load(self, worker: str, inputs: Any):
        """Update the load state for a worker."""
        current_load = self._worker_states.get(worker, {}).get('load', 0)

        # Estimate load based on input size/complexity
        if isinstance(inputs, dict) and 'events' in inputs:
            load_increment = len(inputs['events'])
        elif isinstance(inputs, list):
            load_increment = len(inputs)
        else:
            load_increment = 1

        self._worker_states[worker] = {
            'load': current_load + load_increment,
            'last_updated': time.time()
        }

    def _get_load_distribution(self, workers: List[str]) -> Dict[str, int]:
        """Get current load distribution across workers."""
        return {worker: self._worker_states.get(worker, {}).get('load', 0) for worker in workers}

    def _get_hash_key(self, inputs: Any) -> str:
        """Generate a hash key from inputs for consistent routing."""
        if isinstance(inputs, dict):
            # Use a stable key from the data
            if 'source_id' in inputs:
                return str(inputs['source_id'])
            elif 'id' in inputs:
                return str(inputs['id'])
            else:
                # Hash the entire dict structure
                return str(hash(str(sorted(inputs.items()))))
        else:
            return str(hash(str(inputs)))


class CircuitBreaker(TransformModule):
    """
    Implements circuit breaker pattern for fault tolerance.

    Prevents cascade failures by temporarily stopping requests to
    failing services and allowing them to recover.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._failure_count = 0
        self._last_failure_time = 0
        self._state = 'closed'  # closed, open, half_open

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY, self.DataFormat.PANDAS_DF]
        caps.output_formats = caps.input_formats
        caps.max_latency_ms = 2.0
        caps.real_time_capable = True
        return caps

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Process inputs through circuit breaker logic.

        Args:
            inputs: Input data to process

        Returns:
            Processed data or circuit breaker response
        """
        failure_threshold = self.config.get('failure_threshold', 5)
        recovery_timeout = self.config.get('recovery_timeout', 60.0)
        success_threshold = self.config.get('success_threshold', 3)

        current_time = time.time()

        # Check if we should attempt reset
        if self._state == 'open':
            if current_time - self._last_failure_time > recovery_timeout:
                self._state = 'half_open'
                self._success_count = 0
            else:
                # Circuit is open, fail fast
                return self._create_failure_response("Circuit breaker is open")

        # Attempt processing
        try:
            result = self._process_with_fallback(inputs)

            # Success handling
            if self._state == 'half_open':
                self._success_count += 1
                if self._success_count >= success_threshold:
                    self._state = 'closed'
                    self._failure_count = 0

            return result

        except Exception as e:
            # Failure handling
            self._failure_count += 1
            self._last_failure_time = current_time

            if self._failure_count >= failure_threshold:
                self._state = 'open'

            if self._state == 'half_open':
                self._state = 'open'

            return self._create_failure_response(str(e))

    def _process_with_fallback(self, inputs: Any) -> Any:
        """
        Process inputs with fallback logic.

        In a real implementation, this would delegate to the actual processing.
        For now, it just passes through.
        """
        # Simulate potential failure for demonstration
        if self.config.get('simulate_failure', False) and time.time() % 10 < 2:
            raise Exception("Simulated processing failure")

        return inputs

    def _create_failure_response(self, reason: str) -> Dict[str, Any]:
        """Create a standardized failure response."""
        return {
            'circuit_breaker': {
                'state': self._state,
                'failure_count': self._failure_count,
                'last_failure_time': self._last_failure_time,
                'reason': reason
            },
            'success': False,
            'timestamp': time.time()
        }


class RetryHandler(TransformModule):
    """
    Implements configurable retry logic with exponential backoff.

    Handles transient failures by automatically retrying operations
    with configurable strategies and backoff algorithms.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._retry_counts = {}
        self._backoff_strategy = config.get('backoff_strategy', 'exponential')

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY, self.DataFormat.PANDAS_DF]
        caps.output_formats = caps.input_formats
        caps.max_latency_ms = 1000.0  # Retry operations can be slow
        caps.real_time_capable = False  # Not suitable for hard real-time
        return caps

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Process inputs with retry logic for failed operations.

        Args:
            inputs: Input data that may need retry handling

        Returns:
            Processed data or retry scheduling information
        """
        max_retries = self.config.get('max_retries', 3)
        base_delay = self.config.get('base_delay_ms', 100.0)
        max_delay = self.config.get('max_delay_ms', 10000.0)
        retry_condition = self.config.get('retry_condition', 'failure_detected')

        # Check if retry is needed
        needs_retry = self._check_retry_condition(inputs, retry_condition)

        if not needs_retry:
            return inputs

        request_id = inputs.get('request_id', str(hash(str(inputs))))
        current_retry = self._retry_counts.get(request_id, 0)

        if current_retry >= max_retries:
            return self._create_failure_response(inputs, f"Max retries ({max_retries}) exceeded")

        # Calculate delay for next retry
        delay = self._calculate_delay(current_retry, base_delay, max_delay)

        # Schedule retry
        self._retry_counts[request_id] = current_retry + 1

        return {
            **inputs,
            'retry': {
                'scheduled': True,
                'attempt': current_retry + 1,
                'max_attempts': max_retries,
                'delay_ms': delay,
                'next_retry_at': time.time() + (delay / 1000.0),
                'backoff_strategy': self._backoff_strategy
            }
        }

    def _check_retry_condition(self, inputs: Dict[str, Any], condition: str) -> bool:
        """Check if the inputs meet the retry condition."""
        if condition == 'failure_detected':
            return inputs.get('success', True) == False
        elif condition == 'timeout':
            return inputs.get('timed_out', False) == True
        elif condition == 'error_code':
            error_codes = self.config.get('retry_error_codes', [500, 502, 503, 504])
            return inputs.get('error_code', 0) in error_codes
        return False

    def _calculate_delay(self, attempt: int, base_delay: float, max_delay: float) -> float:
        """Calculate delay for retry attempt using configured backoff strategy."""
        if self._backoff_strategy == 'exponential':
            delay = base_delay * (2 ** attempt)
        elif self._backoff_strategy == 'linear':
            delay = base_delay * (attempt + 1)
        elif self._backoff_strategy == 'fixed':
            delay = base_delay
        else:
            delay = base_delay

        return min(delay, max_delay)

    def _create_failure_response(self, inputs: Dict[str, Any], reason: str) -> Dict[str, Any]:
        """Create a failure response when max retries are exceeded."""
        return {
            **inputs,
            'retry': {
                'exhausted': True,
                'reason': reason,
                'total_attempts': self.config.get('max_retries', 3)
            },
            'success': False,
            'final_failure': True
        }


class RateLimiter(TransformModule):
    """
    Implements rate limiting using token bucket or sliding window algorithms.

    Controls processing throughput to prevent resource exhaustion and
    ensure fair resource allocation across different data streams.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._tokens = {}
        self._last_refill = {}
        self._algorithm = config.get('algorithm', 'token_bucket')

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY, self.DataFormat.PANDAS_DF]
        caps.output_formats = caps.input_formats
        caps.max_latency_ms = 10.0
        caps.real_time_capable = True
        return caps

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Apply rate limiting to input processing.

        Args:
            inputs: Input data to rate limit

        Returns:
            Data with rate limiting decisions
        """
        rate_limit_key = self._get_rate_limit_key(inputs)
        capacity = self.config.get('capacity', 100)
        refill_rate = self.config.get('refill_rate_per_second', 10.0)

        current_time = time.time()

        # Initialize or refill tokens
        if rate_limit_key not in self._tokens:
            self._tokens[rate_limit_key] = capacity
            self._last_refill[rate_limit_key] = current_time
        else:
            # Refill tokens based on time passed
            time_passed = current_time - self._last_refill[rate_limit_key]
            tokens_to_add = time_passed * refill_rate
            self._tokens[rate_limit_key] = min(capacity, self._tokens[rate_limit_key] + tokens_to_add)
            self._last_refill[rate_limit_key] = current_time

        # Check if we can process this request
        if self._tokens[rate_limit_key] >= 1.0:
            # Allow processing
            self._tokens[rate_limit_key] -= 1.0
            return {
                **inputs,
                'rate_limit': {
                    'allowed': True,
                    'remaining_tokens': self._tokens[rate_limit_key],
                    'capacity': capacity
                }
            }
        else:
            # Rate limit exceeded
            wait_time = (1.0 - self._tokens[rate_limit_key]) / refill_rate
            return self._create_rate_limited_response(inputs, wait_time, capacity)

    def _get_rate_limit_key(self, inputs: Dict[str, Any]) -> str:
        """Generate a rate limiting key from inputs."""
        key_field = self.config.get('key_field', 'source')
        default_key = 'default'

        if isinstance(inputs, dict):
            return str(inputs.get(key_field, default_key))
        else:
            return default_key

    def _create_rate_limited_response(self, inputs: Dict[str, Any], wait_time: float, capacity: int) -> Dict[str, Any]:
        """Create a rate-limited response."""
        return {
            **inputs,
            'rate_limit': {
                'allowed': False,
                'wait_time_seconds': wait_time,
                'capacity': capacity,
                'retry_after': time.time() + wait_time
            },
            'rate_limited': True
        }


class CacheManager(TransformModule):
    """
    Intelligent caching layer with TTL and size-based eviction.

    Provides fast access to frequently used data with configurable
    eviction policies and cache invalidation strategies.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self._cache = {}
        self._access_times = {}
        self._creation_times = {}
        self._max_size = config.get('max_cache_size', 1000)
        self._default_ttl = config.get('default_ttl_seconds', 300)

    def _declare_capabilities(self):
        caps = super()._declare_capabilities()
        caps.input_formats = [self.DataFormat.EVENT_TENSOR, self.DataFormat.NUMPY_ARRAY, self.DataFormat.PANDAS_DF]
        caps.output_formats = caps.input_formats
        caps.max_latency_ms = 5.0
        caps.real_time_capable = True
        return caps

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Process inputs with caching support.

        Args:
            inputs: Input data that may be cacheable

        Returns:
            Cached or processed data
        """
        operation = inputs.get('cache_operation', 'get')
        cache_key = self._generate_cache_key(inputs)

        if operation == 'get':
            cached_result = self._get_from_cache(cache_key)
            if cached_result is not None:
                return {
                    **inputs,
                    'cache_hit': True,
                    'cached_data': cached_result['data'],
                    'cache': {
                        'key': cache_key,
                        'age_seconds': time.time() - cached_result['created_at'],
                        'ttl_remaining': self._get_ttl_remaining(cache_key)
                    }
                }
            else:
                # Cache miss - mark for caching on response
                return {
                    **inputs,
                    'cache_hit': False,
                    'cache_key': cache_key
                }

        elif operation == 'set':
            ttl = inputs.get('cache_ttl', self._default_ttl)
            self._set_cache(cache_key, inputs.get('cache_data', inputs), ttl)
            return {
                **inputs,
                'cache_set': True,
                'cache_key': cache_key
            }

        elif operation == 'invalidate':
            self._invalidate_cache(cache_key)
            return {
                **inputs,
                'cache_invalidated': True,
                'cache_key': cache_key
            }

        elif operation == 'clear':
            self._clear_expired()
            return {
                **inputs,
                'cache_cleared': True
            }

        return inputs

    def _generate_cache_key(self, inputs: Dict[str, Any]) -> str:
        """Generate a cache key from inputs."""
        key_fields = self.config.get('key_fields', ['operation', 'parameters'])

        key_parts = []
        for field in key_fields:
            if field in inputs:
                key_parts.append(f"{field}:{inputs[field]}")

        if key_parts:
            return "|".join(key_parts)
        else:
            return str(hash(str(sorted(inputs.items()))))

    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve item from cache if valid."""
        if key not in self._cache:
            return None

        # Check TTL
        if time.time() - self._creation_times[key] > self._cache[key]['ttl']:
            self._invalidate_cache(key)
            return None

        # Update access time
        self._access_times[key] = time.time()
        return self._cache[key]

    def _set_cache(self, key: str, data: Any, ttl: float):
        """Store item in cache with TTL."""
        current_time = time.time()

        self._cache[key] = {
            'data': data,
            'ttl': ttl,
            'created_at': current_time
        }
        self._access_times[key] = current_time
        self._creation_times[key] = current_time

        # Evict if over capacity (simple LRU)
        self._evict_if_needed()

    def _invalidate_cache(self, key: str):
        """Remove item from cache."""
        self._cache.pop(key, None)
        self._access_times.pop(key, None)
        self._creation_times.pop(key, None)

    def _evict_if_needed(self):
        """Evict items if cache is over capacity."""
        while len(self._cache) > self._max_size:
            # Find least recently used
            oldest_key = min(self._access_times, key=self._access_times.get)
            self._invalidate_cache(oldest_key)

    def _clear_expired(self):
        """Clear all expired cache entries."""
        current_time = time.time()
        expired_keys = []

        for key, entry in self._cache.items():
            if current_time - self._creation_times[key] > entry['ttl']:
                expired_keys.append(key)

        for key in expired_keys:
            self._invalidate_cache(key)

    def _get_ttl_remaining(self, key: str) -> float:
        """Get remaining TTL for a cache key."""
        if key not in self._cache:
            return 0.0

        elapsed = time.time() - self._creation_times[key]
        return max(0.0, self._cache[key]['ttl'] - elapsed)