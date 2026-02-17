"""
Example functional module demonstrating the base architecture.

This shows how to create a simple processing module that filters event data.
"""

from typing import Any, Dict, Union
from .base import ProcessingModule, ModuleConfigurationError


class EventFilterModule(ProcessingModule):
    """
    Example functional module that filters events based on threshold.

    This demonstrates how to extend ProcessingModule to create custom
    functional components for neuromorphic applications.
    """

    def _declare_capabilities(self):
        return super()._declare_capabilities()

    def _declare_requirements(self):
        return super()._declare_requirements()

    def _validate_config(self, config: Dict[str, Any]) -> None:
        allowed = {"name", "version", "threshold"}
        unknown = set(config) - allowed
        if unknown:
            raise ModuleConfigurationError(f"Unsupported configuration keys: {sorted(unknown)}")

        threshold = config.get("threshold", 0.5)
        if not isinstance(threshold, (int, float)):
            raise ModuleConfigurationError("threshold must be numeric")

    def process(self, inputs: Union[Any, Dict[str, Any]]) -> Union[Any, Dict[str, Any]]:
        """
        Filter events based on amplitude threshold.

        Args:
            inputs: Event data (could be EventTensor or dict)

        Returns:
            Filtered event data
        """
        threshold = self.config.get('threshold', 0.5)

        if isinstance(inputs, dict):
            # Handle dictionary input (e.g., from sensors)
            if 'events' in inputs:
                filtered_events = [
                    event for event in inputs['events']
                    if abs(event.get('amplitude', 0)) > threshold
                ]
                return {'events': filtered_events, 'filtered_count': len(inputs['events']) - len(filtered_events)}
            else:
                return inputs
        else:
            # Handle direct event data
            # For now, return as-is (in real implementation, would filter EventTensor)
            return inputs


# Example usage
if __name__ == "__main__":
    # Create module configuration
    config = {
        'name': 'event_filter',
        'version': '1.0.0',
        'threshold': 0.7  # Filter events below 0.7 amplitude
    }

    # Create and initialize module
    filter_module = EventFilterModule(config)
    print("Module capabilities:", filter_module.get_metadata()['capabilities'])

    # Example input data
    sample_events = [
        {'timestamp': 1000, 'x': 10, 'y': 20, 'amplitude': 0.3},
        {'timestamp': 1001, 'x': 15, 'y': 25, 'amplitude': 0.8},
        {'timestamp': 1002, 'x': 12, 'y': 18, 'amplitude': 0.2},
        {'timestamp': 1003, 'x': 20, 'y': 30, 'amplitude': 0.9}
    ]

    # Process events
    result = filter_module.process({'events': sample_events})
    print(f"Original events: {len(sample_events)}")
    print(f"Filtered events: {len(result['events'])}")
    print(f"Events filtered out: {result['filtered_count']}")
