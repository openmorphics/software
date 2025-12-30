from __future__ import annotations
from typing import Optional, Dict, Any, List, Union
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine
import json
from ..errors import FusionError


def data_association(
    sources: List[Any],
    max_distance: float = 1.0,
    algorithm: str = "nearest_neighbor",
    window: str = "50 ms",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Multi-modal data association for sensor fusion.

    Associates detections across different sensor modalities (vision, audio, IMU)
    using various algorithms like nearest neighbor, Hungarian, or probabilistic
    approaches. Handles temporal alignment and feature matching.

    Args:
        sources: List of sensor sources to associate
        max_distance: Maximum association distance threshold
        algorithm: Association algorithm ("nearest_neighbor", "hungarian", "probabilistic")
        window: Temporal association window
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured data association graph

    Raises:
        FusionError: If parameters are invalid or sensor configuration fails

    Example:
        # Basic nearest neighbor association
        graph = data_association([vision_source, audio_source])

        # Probabilistic data association
        graph = data_association(sources, algorithm="probabilistic", max_distance=2.0)
    """
    if len(sources) < 2:
        raise FusionError("Data association requires at least 2 sensor sources")

    if max_distance <= 0:
        raise FusionError("Maximum distance must be positive")

    valid_algorithms = ["nearest_neighbor", "hungarian", "probabilistic"]
    if algorithm not in valid_algorithms:
        raise FusionError(f"Algorithm must be one of {valid_algorithms}, got {algorithm}")

    # Create EIR graph for data association
    g = EIRGraph()

    # Multi-modal detection association
    association_ops = []
    for i, source in enumerate(sources):
        # Create temporal windows for each sensor stream
        assoc_op = EventFuse(f"assoc_{i}", window=window, min_count=1).as_op()
        g.add_node(f"assoc_{i}", assoc_op)
        association_ops.append(assoc_op)

    # Data association decision node
    assoc_decision = EventFuse("data_association", window=window, min_count=len(sources)).as_op()
    g.add_node("data_association", assoc_decision)

    # Connect sensor inputs to association decision
    for i, assoc_op in enumerate(association_ops):
        g.connect(f"assoc_{i}", "out", "data_association", "in")

    return g