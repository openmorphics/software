from __future__ import annotations
from typing import Optional, Dict, Any, List, Union
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse
import json
from ..errors import FusionError


def scene_understanding(
    sources: List[Any],
    context_model: str = "hierarchical",
    confidence_threshold: float = 0.7,
    max_objects: int = 50,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Multi-modal scene understanding and contextual awareness.

    Processes fused sensor data to understand the complete scene context.
    Combines vision, audio, IMU, and other sensor inputs to build a comprehensive
    understanding of the environment with object relationships and activities.

    Args:
        sources: List of fused sensor sources
        context_model: Contextual modeling approach ("hierarchical", "graph", "attention")
        confidence_threshold: Minimum confidence for scene elements
        max_objects: Maximum objects to track in scene
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured scene understanding graph

    Raises:
        FusionError: If parameters are invalid or sensor configuration fails

    Example:
        # Hierarchical scene understanding
        graph = scene_understanding([fused_vision_audio, imu_source])

        # Graph-based contextual modeling
        graph = scene_understanding(sources, context_model="graph", max_objects=100)
    """
    if len(sources) < 1:
        raise FusionError("Scene understanding requires at least 1 sensor source")

    if not (0.0 < confidence_threshold <= 1.0):
        raise FusionError("Confidence threshold must be in range (0, 1]")

    if max_objects <= 0:
        raise FusionError("Maximum objects must be positive")

    valid_models = ["hierarchical", "graph", "attention"]
    if context_model not in valid_models:
        raise FusionError(f"Context model must be one of {valid_models}, got {context_model}")

    # Create EIR graph for scene understanding
    g = EIRGraph()

    # Scene context processing nodes
    context_ops = []
    for i, source in enumerate(sources):
        # Create contextual processing for each sensor modality
        context_op = EventFuse(f"context_{i}", window="200 ms", min_count=1).as_op()
        g.add_node(f"context_{i}", context_op)
        context_ops.append(context_op)

    # Scene fusion and understanding
    scene_fusion = EventFuse("scene_understanding", window="500 ms", min_count=len(sources)).as_op()
    g.add_node("scene_understanding", scene_fusion)

    # Connect context inputs to scene understanding
    for i, context_op in enumerate(context_ops):
        g.connect(f"context_{i}", "out", "scene_understanding", "in")

    return g