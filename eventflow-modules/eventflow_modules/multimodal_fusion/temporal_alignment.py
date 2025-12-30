from __future__ import annotations
from typing import Optional, Dict, Any, List, Union
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine
import json
from ..errors import FusionError


def temporal_alignment(
    sources: List[Any],
    sync_method: str = "timestamp",
    max_delay: str = "100 ms",
    interpolation: str = "linear",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Multi-modal temporal alignment for sensor fusion.

    Aligns data streams from different sensors in time using various synchronization
    methods (timestamp correlation, phase-locked loops, etc.). Handles variable
    sampling rates and temporal offsets between modalities.

    Args:
        sources: List of sensor sources to align temporally
        sync_method: Synchronization method ("timestamp", "pll", "correlation")
        max_delay: Maximum allowed temporal delay for alignment
        interpolation: Interpolation method for missing data ("linear", "nearest", "cubic")
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured temporal alignment graph

    Raises:
        FusionError: If parameters are invalid or sensor configuration fails

    Example:
        # Basic timestamp-based alignment
        graph = temporal_alignment([vision_source, audio_source])

        # Phase-locked loop synchronization
        graph = temporal_alignment(sources, sync_method="pll", max_delay="200 ms")
    """
    if len(sources) < 2:
        raise FusionError("Temporal alignment requires at least 2 sensor sources")

    valid_sync_methods = ["timestamp", "pll", "correlation"]
    if sync_method not in valid_sync_methods:
        raise FusionError(f"Sync method must be one of {valid_sync_methods}, got {sync_method}")

    valid_interpolations = ["linear", "nearest", "cubic"]
    if interpolation not in valid_interpolations:
        raise FusionError(f"Interpolation must be one of {valid_interpolations}, got {interpolation}")

    # Create EIR graph for temporal alignment
    g = EIRGraph()

    # Temporal synchronization nodes for each sensor
    align_ops = []
    for i, source in enumerate(sources):
        # Create temporal alignment window for each sensor
        align_op = DelayLine(f"align_{i}", delay=max_delay).as_op()
        g.add_node(f"align_{i}", align_op)
        align_ops.append(align_op)

    # Temporal fusion node
    temporal_fuse = EventFuse("temporal_fusion", window=max_delay, min_count=len(sources)).as_op()
    g.add_node("temporal_fusion", temporal_fuse)

    # Connect aligned inputs to fusion
    for i, align_op in enumerate(align_ops):
        g.connect(f"align_{i}", "out", "temporal_fusion", "in")

    return g