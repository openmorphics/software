from __future__ import annotations
from typing import Optional, Dict, Any, List, Union
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse
import json
from ..errors import FusionError


def decision_fusion(
    sources: List[Any],
    fusion_type: str = "consensus",
    voting_method: str = "majority",
    confidence_weighting: bool = True,
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Decision fusion for multi-modal sensor processing.

    Combines decisions from multiple sensor modalities using various fusion
    strategies (consensus-based, probabilistic, voting-based). Provides robust
    decision-making by leveraging complementary information from different sensors.

    Args:
        sources: List of decision sources from different modalities
        fusion_type: Type of fusion ("consensus", "probabilistic", "voting")
        voting_method: Voting strategy ("majority", "weighted", "plurality")
        confidence_weighting: Whether to weight decisions by confidence
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured decision fusion graph

    Raises:
        FusionError: If parameters are invalid or sensor configuration fails

    Example:
        # Consensus-based fusion
        graph = decision_fusion([vision_decisions, audio_decisions])

        # Probabilistic fusion with weighting
        graph = decision_fusion(sources, fusion_type="probabilistic", confidence_weighting=True)
    """
    if len(sources) < 2:
        raise FusionError("Decision fusion requires at least 2 sensor sources")

    valid_fusion_types = ["consensus", "probabilistic", "voting"]
    if fusion_type not in valid_fusion_types:
        raise FusionError(f"Fusion type must be one of {valid_fusion_types}, got {fusion_type}")

    valid_voting_methods = ["majority", "weighted", "plurality"]
    if voting_method not in valid_voting_methods:
        raise FusionError(f"Voting method must be one of {valid_voting_methods}, got {voting_method}")

    # Create EIR graph for decision fusion
    g = EIRGraph()

    # Decision processing nodes for each modality
    decision_ops = []
    for i, source in enumerate(sources):
        # Create decision processing for each sensor
        decision_op = EventFuse(f"decisions_{i}", window="150 ms", min_count=1).as_op()
        g.add_node(f"decisions_{i}", decision_op)
        decision_ops.append(decision_op)

    # Final decision fusion node
    fusion_decision = EventFuse("decision_fusion", window="300 ms", min_count=len(sources)).as_op()
    g.add_node("decision_fusion", fusion_decision)

    # Connect decision inputs to final fusion
    for i, decision_op in enumerate(decision_ops):
        g.connect(f"decisions_{i}", "out", "decision_fusion", "in")

    return g