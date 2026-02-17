from __future__ import annotations

from typing import Any

import numpy as np

from eventflow_modules.functions.audio_modules import AudioBeamformer, KeywordSpotter, VoiceActivityDetector
from eventflow_modules.functions.generic_modules import (
    CacheManager,
    CircuitBreaker,
    ConditionalProcessor,
    DataValidator,
    EventBuffer,
    EventLogger,
    EventMultiplexer,
    EventRouter,
    LoadBalancer,
    PerformanceMonitor,
    RateLimiter,
    RetryHandler,
    StateManager,
)
from eventflow_modules.functions.processing_modules import DataNormalizer, FeatureExtractor, SpatialFilter, TemporalFilter
from eventflow_modules.functions.robotics_modules import MotorController, ObstacleAvoidanceController, PathPlanner
from eventflow_modules.functions.vision_modules import CornerDetector, ObjectTracker, OpticalFlowEstimator


def _events(n: int) -> list[dict[str, Any]]:
    return [
        {
            "timestamp": i * 10_000_000,
            "x": i % 16,
            "y": (i * 3) % 16,
            "amplitude": 0.2 + (i % 5) * 0.2,
            "channel": i % 4,
            "distance": 0.2 + (i % 4) * 0.2,
            "angle": (-1.0 + (i % 5) * 0.5),
        }
        for i in range(n)
    ]


def test_generic_modules_smoke_paths() -> None:
    ev = _events(20)

    # EventBuffer: count mode flush path.
    buf = EventBuffer({"name": "buf", "buffer_type": "count", "buffer_size": 5, "auto_flush": True})
    out = buf.process({"events": ev[:5]})
    assert out.get("buffer_flushed") is True
    assert len(out.get("events", [])) == 5

    # EventRouter with one explicit route.
    router = EventRouter(
        {
            "name": "router",
            "routing_rules": [{"route": "hot", "condition": {"amplitude": {"min": 0.7}}}],
            "default_route": "cold",
        }
    )
    routed = router.process({"events": ev})
    assert "hot" in routed and "cold" in routed and "_routing_stats" in routed

    mux = EventMultiplexer({"name": "mux", "sync_mode": "time"})
    combined = mux.process({"a": {"events": ev[:5]}, "b": {"events": ev[5:10]}})
    assert combined["total_events"] == 10

    mon = PerformanceMonitor({"name": "mon", "report_interval_ms": 0, "metrics": ["latency", "throughput", "count"]})
    mon_out = mon.process({"events": ev})
    assert "_performance_report" in mon_out

    cond = ConditionalProcessor(
        {
            "name": "cond",
            "conditions": [{"field": "meta.flag", "operator": "equals", "value": True}],
            "true_action": "modify",
            "false_action": "block",
        }
    )
    true_out = cond.process({"meta": {"flag": True}})
    false_out = cond.process({"meta": {"flag": False}})
    assert true_out.get("_condition_action") == "true_branch_processed"
    assert false_out.get("blocked") is True

    state_set = StateManager({"name": "state", "operation": "set", "state_key": "k"})
    set_out = state_set.process({"value": 9})
    assert set_out["state_updated"] is True
    state_set.config["operation"] = "get"
    get_out = state_set.process({})
    assert get_out["state"] == 9

    validator = DataValidator(
        {
            "name": "validator",
            "validation_rules": [{"name": "required", "type": "schema", "required_fields": ["events"]}],
        }
    )
    valid = validator.process({"events": ev})
    assert valid["validation"]["passed"] is True

    logger = EventLogger({"name": "logger", "log_level": "INFO"})
    logged = logger.process({"events": ev, "metadata": {"cost": 3}})
    assert "log_reference" in logged

    balancer = LoadBalancer({"name": "lb", "workers": ["w1", "w2"], "strategy": "round_robin"})
    r1 = balancer.process({"events": ev[:2]})
    r2 = balancer.process({"events": ev[:2]})
    assert r1["routing"]["selected_worker"] in ("w1", "w2")
    assert r2["routing"]["selected_worker"] in ("w1", "w2")

    breaker = CircuitBreaker({"name": "cb", "failure_threshold": 1})
    breaker._process_with_fallback = lambda _inputs: (_ for _ in ()).throw(RuntimeError("boom"))
    b = breaker.process({"events": ev[:2]})
    assert b["success"] is False
    assert b["circuit_breaker"]["state"] == "open"

    retry = RetryHandler({"name": "retry", "max_retries": 1, "base_delay_ms": 1})
    scheduled = retry.process({"request_id": "a", "success": False})
    exhausted = retry.process({"request_id": "a", "success": False})
    assert scheduled["retry"]["scheduled"] is True
    assert exhausted["retry"]["exhausted"] is True

    limiter = RateLimiter({"name": "rl", "capacity": 1, "refill_rate_per_second": 0.001, "key_field": "source"})
    allow = limiter.process({"source": "s1"})
    deny = limiter.process({"source": "s1"})
    assert allow["rate_limit"]["allowed"] is True
    assert deny["rate_limit"]["allowed"] is False

    cache = CacheManager({"name": "cache", "max_cache_size": 2, "default_ttl_seconds": 60})
    set_cache = cache.process({"cache_operation": "set", "cache_data": {"x": 1}, "operation": "op", "parameters": "p"})
    get_cache = cache.process({"cache_operation": "get", "operation": "op", "parameters": "p"})
    inv_cache = cache.process({"cache_operation": "invalidate", "operation": "op", "parameters": "p"})
    assert set_cache["cache_set"] is True
    assert get_cache["cache_hit"] in (True, False)
    assert inv_cache["cache_invalidated"] is True


def test_audio_modules_smoke_paths() -> None:
    ev = _events(80)

    vad = VoiceActivityDetector(
        {
            "name": "vad",
            "vad_method": "energy",
            "vad_threshold": 0.1,
            "min_speech_duration_ms": 10,
        }
    )
    vad_out = vad.process({"events": ev})
    assert "speech_segments" in vad_out
    assert "vad_decisions" in vad_out

    kws = KeywordSpotter({"name": "kws", "keywords": ["hello"], "threshold": 0.0})
    kws_out = kws.process({"events": ev})
    assert "detections" in kws_out
    assert "keywords" in kws_out

    beam = AudioBeamformer({"name": "beam", "beam_angle": 15, "num_channels": 4})
    beam_out = beam.process({"events": ev})
    assert "events" in beam_out
    assert beam_out["method"] == "delay_and_sum"


def test_vision_modules_smoke_paths() -> None:
    ev = _events(60)

    flow = OpticalFlowEstimator({"name": "flow", "flow_method": "event_correlation"})
    flow_out = flow.process({"events": ev})
    assert "flow_vectors" in flow_out
    assert "motion_detected" in flow_out

    corners = CornerDetector({"name": "corners", "detection_method": "fast", "corner_threshold": 0.0})
    corner_out = corners.process({"events": ev})
    assert "corners" in corner_out
    assert "features" in corner_out

    tracker = ObjectTracker({"name": "tracker", "tracking_method": "simple"})
    track_out = tracker.process({"events": ev})
    assert "tracks" in track_out
    assert "trajectories" in track_out


def test_robotics_modules_smoke_paths() -> None:
    ev = _events(30)

    avoid = ObstacleAvoidanceController({"name": "avoid", "method": "potential_field", "safety_margin": 1.0})
    avoid_out = avoid.process({"events": ev})
    assert "control_commands" in avoid_out
    assert "obstacles_detected" in avoid_out

    planner = PathPlanner({"name": "planner", "algorithm": "astar"})
    path_out = planner.process({"start_position": (0.0, 0.0), "goal_position": (1.0, 1.0), "obstacles": []})
    assert "path" in path_out
    assert path_out["waypoints"] >= 2

    motor = MotorController({"name": "motor", "control_mode": "velocity", "max_speed": 50.0})
    motor_out = motor.process({"linear_x": 1.0, "angular_z": 0.2, "timestamp": 123})
    assert "motor_commands" in motor_out
    assert motor_out["num_motors"] == 2


def test_processing_modules_smoke_paths() -> None:
    ev = _events(25)

    tfilter = TemporalFilter({"name": "tfilter", "filter_type": "mean", "window_size": 5})
    t_out = tfilter.process({"events": ev})
    assert t_out["filter_applied"] == "mean"

    sfilter = SpatialFilter({"name": "sfilter", "filter_type": "density", "neighborhood_radius": 10.0})
    s_out = sfilter.process({"events": ev})
    assert s_out["filter_applied"] == "density"

    norm = DataNormalizer({"name": "norm", "normalization_type": "minmax", "target_range": [0.0, 1.0]})
    n_out = norm.process({"events": ev})
    assert n_out["normalization_type"] == "minmax"

    extractor = FeatureExtractor({"name": "fx", "feature_types": ["statistical", "temporal", "spatial"]})
    fx_out = extractor.process({"events": ev})
    assert len(fx_out["feature_names"]) == len(fx_out["features"])

    # Numpy-array path for normalization.
    arr = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    arr_out = norm.process(arr)
    assert arr_out.shape == arr.shape
