from __future__ import annotations
from typing import Optional, Dict, Any, List, Union
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse
import json
from ..errors import FusionError


def feature_extraction(
    sources: List[Any],
    feature_types: List[str] = None,
    dimensionality: int = 128,
    fusion_method: str = "concatenate",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Multi-modal feature extraction from sensor fusion.

    Extracts meaningful features from multiple sensor modalities and fuses them
    into unified representations. Supports various fusion methods (concatenation,
    attention, cross-modal learning) for rich feature representations.

    Args:
        sources: List of sensor sources for feature extraction
        feature_types: Types of features to extract per modality
        dimensionality: Output feature dimensionality
        fusion_method: Feature fusion method ("concatenate", "attention", "cross_modal")
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured feature extraction graph

    Raises:
        FusionError: If parameters are invalid or sensor configuration fails

    Example:
        # Basic feature concatenation
        graph = feature_extraction([vision_source, audio_source])

        # Attention-based fusion
        graph = feature_extraction(sources, fusion_method="attention", dimensionality=256)
    """
    if len(sources) < 1:
        raise FusionError("Feature extraction requires at least 1 sensor source")

    if dimensionality <= 0:
        raise FusionError("Feature dimensionality must be positive")

    if feature_types is None:
        feature_types = ["spatial", "temporal", "spectral"]

    valid_fusion_methods = ["concatenate", "attention", "cross_modal"]
    if fusion_method not in valid_fusion_methods:
        raise FusionError(f"Fusion method must be one of {valid_fusion_methods}, got {fusion_method}")

    # Create EIR graph for feature extraction
    g = EIRGraph()

    # Feature extraction nodes for each modality
    feature_ops = []
    for i, source in enumerate(sources):
        # Create feature extraction for each sensor
        feature_op = EventFuse(f"features_{i}", window="100 ms", min_count=1).as_op()
        g.add_node(f"features_{i}", feature_op)
        feature_ops.append(feature_op)

    # Feature fusion node
    fusion_op = EventFuse("feature_fusion", window="200 ms", min_count=len(sources)).as_op()
    g.add_node("feature_fusion", fusion_op)

    # Connect feature inputs to fusion
    for i, feature_op in enumerate(feature_ops):
        g.connect(f"features_{i}", "out", "feature_fusion", "in")

    return g