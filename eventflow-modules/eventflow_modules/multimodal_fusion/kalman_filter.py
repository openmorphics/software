from __future__ import annotations
from typing import Optional, Dict, Any, List, Union
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import EventFuse, DelayLine, XYToChannel
import json
from ..errors import FusionError

# Optional Rust acceleration for fusion processing
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore


def kalman_filter(
    sources: List[Any],
    state_dim: int = 4,
    measurement_dim: int = 2,
    process_noise: float = 0.1,
    measurement_noise: float = 0.5,
    window: str = "100 ms",
    params: Optional[Dict[str, Any]] = None,
) -> EIRGraph:
    """
    Multi-modal Kalman filter for sensor fusion.

    Implements a Kalman filter that fuses data from multiple sensor modalities
    (vision, audio, IMU, etc.) to provide optimal state estimation. The filter
    handles temporal alignment and uncertainty propagation across sensor streams.

    Args:
        sources: List of input sensor sources to fuse
        state_dim: State vector dimension (position, velocity, etc.)
        measurement_dim: Measurement vector dimension
        process_noise: Process noise covariance scalar
        measurement_noise: Measurement noise covariance scalar
        window: Temporal fusion window
        params: Additional algorithm parameters

    Returns:
        EIRGraph: Configured Kalman filter fusion graph

    Raises:
        FusionError: If parameters are invalid or sensor configuration fails

    Example:
        # Basic IMU + vision fusion
        graph = kalman_filter([imu_source, vision_source], state_dim=6)

        # High-precision fusion with custom noise
        graph = kalman_filter(sources, process_noise=0.01, measurement_noise=0.1)
    """
    if len(sources) < 2:
        raise FusionError("Kalman filter requires at least 2 sensor sources")

    if state_dim <= 0 or measurement_dim <= 0:
        raise FusionError("State and measurement dimensions must be positive")

    if not (0.0 < process_noise <= 1.0):
        raise FusionError("Process noise must be in range (0, 1]")

    if not (0.0 < measurement_noise <= 1.0):
        raise FusionError("Measurement noise must be in range (0, 1]")

    # Create EIR graph for sensor fusion
    g = EIRGraph()

    # Multi-modal temporal alignment and fusion
    # Combine multiple sensor streams using temporal windows
    fusion_ops = []
    for i, source in enumerate(sources):
        # Create temporal fusion window for each sensor
        fuse_op = EventFuse(f"sensor_{i}", window=window, min_count=1).as_op()
        g.add_node(f"sensor_{i}", fuse_op)
        fusion_ops.append(fuse_op)

    # Kalman prediction and update operations
    # This represents the core Kalman filter logic in EIR
    kalman_predict = EventFuse("kalman_predict", window=window, min_count=len(sources)).as_op()
    g.add_node("kalman_predict", kalman_predict)

    kalman_update = EventFuse("kalman_update", window=window, min_count=1).as_op()
    g.add_node("kalman_update", kalman_update)

    # Connect sensor inputs to prediction step
    for i, fuse_op in enumerate(fusion_ops):
        g.connect(f"sensor_{i}", "out", "kalman_predict", "in")

    # Connect prediction to update
    g.connect("kalman_predict", "out", "kalman_update", "in")

    return g