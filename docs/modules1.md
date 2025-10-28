EventFlow Modules — Comprehensive Analysis, Gaps, and Expansion Plan

Scope
- Assessed current modules in eventflow-modules by reading sources and tests.
- Evaluated completeness, robustness, integration with core and SAL, test coverage, and documentation.
- Produced concrete enhancement plans and a prioritized backlog of 12 proposed modules with interfaces, dependencies, testing strategies, and ecosystem impact.

1) Current state and completeness

Audio
- Frontends:
  - [stft_frontend()](eventflow-modules/eventflow_modules/audio/frontend.py:6): builds STFT-only graph; connects no downstream nodes; input is PCM-like events; OK for prototypes.
  - [mel_frontend()](eventflow-modules/eventflow_modules/audio/frontend.py:22): STFT -> Mel; parameterizable; deterministic software ops; good baseline.
- Pipelines:
  - [voice_activity()](eventflow-modules/eventflow_modules/audio/vad.py:6): STFT -> Mel -> EventFuse self-coincidence; minimal VAD proxy; lacks adaptive thresholding/noise gating.
  - [keyword_spotter()](eventflow-modules/eventflow_modules/audio/kws.py:6): STFT -> Mel -> LIF; minimal; no templates/LM/hysteresis; trait: spikes driven by mel energy.
  - [diarization()](eventflow-modules/eventflow_modules/audio/diarization.py:6): STFT -> Mel -> EventFuse over long window; coarse segmentation proxy.
  - [localization()](eventflow-modules/eventflow_modules/audio/localization.py:6): STFT -> Mel -> EventFuse; acts as band co-activity proxy; not true DOA.
- Gaps:
  - No multi-channel/array handling beyond conceptual “mic_array_source”.
  - Missing adaptive thresholds, VAD hangover, noise estimation.
  - No GCC-PHAT, beamforming, onset detection ops.

Vision
- Primitives:
  - [optical_flow()](eventflow-modules/eventflow_modules/vision/optical_flow.py:6): XYToChannel → Shift±x + Delay → EventFuse; minimal motion proxy; directions limited to E/W.
  - [corner_tracking()](eventflow-modules/eventflow_modules/vision/corner_tracking.py:6): XYToChannel → Shift East/North → EventFuse; simple corner proxy.
  - [object_tracking()](eventflow-modules/eventflow_modules/vision/object_tracking.py:6): XYToChannel → Delay self-coincidence; persistence proxy.
  - [gesture_detect()](eventflow-modules/eventflow_modules/vision/gesture_detect.py:5): EventFuse node only; expects upstream flow features; no template matching.
- Gaps:
  - No S/N/E/W/NE/NW/SE/SW dense shifts; no time surfaces; no clustering; no corner non-maximum suppression; sparse directionality.

Robotics
- [event_slam()](eventflow-modules/eventflow_modules/robotics/slam.py:6): XYToChannel fused with delayed IMU; simple correlation proxy; useful sample but not a SLAM system.
- [reflex_controller()](eventflow-modules/eventflow_modules/robotics/reflex.py:5): single LIF node; scaffold only.

Time series
- [change_point()](eventflow-modules/eventflow_modules/timeseries/change_point.py:6): Delay + EventFuse self-coincidence; proxy for burst/change.
- [spike_pattern_mining()](eventflow-modules/eventflow_modules/timeseries/spike_mining.py:6): Delay + EventFuse; minimal frequent pattern proxy.
- [anomaly_detector()](eventflow-modules/eventflow_modules/timeseries/anomaly.py:5): LIF threshold only; extremely minimal.

Wellness and creative
- [sleep_staging()](eventflow-modules/eventflow_modules/wellness/sleep.py:6), [stress_index()](eventflow-modules/eventflow_modules/wellness/stress.py:6), [hrv_index()](eventflow-modules/eventflow_modules/wellness/hrv.py:5): delay/fuse placeholders; no HRV intervals or band-pass; no physiological units.
- [bio_sequencer()](eventflow-modules/eventflow_modules/creative/sequencer.py:6) and [event_graphics()](eventflow-modules/eventflow_modules/creative/graphics.py:6): identity/delay scaffolds.

2) Robustness and architectural observations

- Strengths:
  - All modules return typed EIR graphs using deterministic core ops (EIRGraph and ops).
  - Consistent, compositional style; parameters are passed in dicts.
  - Minimal functions and tests run end-to-end via core runtime.

- Weaknesses:
  - Sparse parameter validation; no clear schema for params.
  - Many functions ignore their “source” parameters and rely on runtime wiring; OK but confusing in signatures.
  - No explicit units/dimensions in module metadata; downstream interpretability can suffer.
  - Few directions in motion (vision); no threshold adaptation; no device capability awareness.

3) Integration patterns with core and SAL

- Modules depend on core EIR types and ops:
  - EIR: [EIRGraph](eventflow-core/eventflow_core/eir/graph.py:1)
  - Ops used widely: EventFuse, DelayLine, XYToChannel, ShiftXY, STFT, MelBands, LIFNeuron (all in [ops.py](eventflow-core/eventflow_core/eir/ops.py:1))
- Execution is typically done with [run_event_mode()](eventflow-core/eventflow_core/runtime/exec.py:7) in tests.
- SAL integration is indirect: SAL produces Event Tensor JSONL traces (via [stream_to_jsonl()](eventflow-sal/api.py:195)), then CLI run merges module EIR with traces. There are no direct SAL bindings in modules, which is appropriate (keep domain graphs backend-agnostic).

4) Test coverage and documentation quality

- Tests exist and pass:
  - Audio: [TestAudioModules](eventflow-modules/tests/test_audio_modules.py:12) includes [test_stft_frontend_bin()](eventflow-modules/tests/test_audio_modules.py:13), [test_vad_pipeline_outputs()](eventflow-modules/tests/test_audio_modules.py:26), [test_kws_builds_and_runs()](eventflow-modules/tests/test_audio_modules.py:34)
  - Domains: [TestVisionModules](eventflow-modules/tests/test_domain_modules.py:28), [TestRoboticsModules](eventflow-modules/tests/test_domain_modules.py:54), [TestTimeseriesWellnessCreative](eventflow-modules/tests/test_domain_modules.py:66)
- Test depth:
  - Primarily existence/length assertions; minimal correctness checks.
  - No golden trace comparisons for modules; no stress/latency/power/dropped-event metrics.
- Documentation:
  - Package README is a placeholder ([README.md](eventflow-modules/README.md:1)); per-module docstrings are minimal or absent.
  - No module usage guide or param schemas.

5) Immediate enhancement plan (existing modules)

Cross-cutting (apply to all modules in this package)
- Add comprehensive docstrings with I/O conventions, expected event shapes, dims, units.
- Introduce parameter dataclasses or “params schema” dicts with default values and validation (type/range).
- Ensure each function uses or clearly documents its “source” argument; alternatively remove unused inputs from signatures and document runtime wiring conventions.
- Standardize node names and ports (“in”, “out”, “a”, “b”, “spec”, “mel”, “ch”) and document them.
- Add unit-checked metadata to graphs where applicable (e.g., value units).
- Provide golden traces for reference inputs for each module; add compare-traces tests using [compare_traces_jsonl()](eventflow-core/conformance/comparator.py:60).
- Add edge-case tests (empty streams, high-rate overload, extreme window sizes); add property-based tests for ordering invariants.

Module-specific
- Audio
  - voice_activity(): Add adaptive thresholding (short-term energy estimator) using a MelBands moving average op or a LIF leak baseline; expose hangover time; test with silence and varying SNR.
  - keyword_spotter(): Add a simple template integrator (DelayLine + multi-band weighting) before LIF; doc example for “hey eventflow”.
  - localization(): Accept multi-channel inputs; add per-channel STFT nodes and a combine stage (start with simple band co-activity; in roadmap add GCC-PHAT).
- Vision
  - optical_flow(): Expand to 8-directional shifts; emit directional channels; add tests for E/W/N/S; param to control shifts radius.
  - corner_tracking(): Add non-max suppression (proxy via EventFuse thresholds across orthogonal shifts and a refractory DelayLine).
  - object_tracking(): Add hysteresis; ensure track decays after timeout (DelayLine thresholds).
- Robotics
  - event_slam(): Add proper IMU low-pass or quantization to align with DVS timing; add tests for misalignment; expose window and min_count defaults tuned to examples.
  - reflex_controller(): Add input thresholding and refractory.
- Time series
  - anomaly_detector(): Use EWMA/LIF leak baseline; test step changes; expose tau and thresholds.
  - change_point() / spike_pattern_mining(): Provide directionality or separate increase/decrease detection by dual delays.
- Wellness
  - hrv_index(): Replace plain DelayLine with interval extractor (proposal below); until new op lands, compute inter-beat delay proxy by EventFuse at harmonics; add tests with synthetic RR intervals.
- Creative
  - bio_sequencer(): Add random seedable pattern variation; map indices to MIDI channels via metadata.

6) Proposed new core ops to unlock richer modules (tracked in core)
- ExpDecay/TimeSurface: exponential integration of recent activity (vision/time series).
- AdaptiveThreshold: baseline tracking for audio/VAD and anomaly detection.
- CoincidenceN: EventFuse generalized to N inputs with min_count parameter exposed across more than two ports.
- CrossCorr/GCCPHAT: audio DOA primitives.
- IntervalEstimator: emits intervals between events (needed for HRV).
- Cluster2D: online clustering in XY space (vision segmentation).

7) Prioritized new modules (12 proposals)

1. Vision: time_surface(source, tau_ms)
- Purpose: produce per-pixel decaying activity maps enabling robust flow/corner detection.
- Interface: def time_surface(source: Any, tau_ms: int = 30, params: dict | None = None) -> EIRGraph
- Dependencies: Proposed ExpDecay op; XYToChannel.
- Tests: Synthetic DVS stream with moving point; assert surface decays and follows motion; golden trace.
- Ecosystem impact: foundational feature for event-based vision pipelines.

2. Vision: optical_flow_dense(source, directions=8, window="2 ms")
- Purpose: extend optical_flow to 8 directions and configurable shift radii.
- Interface: def optical_flow_dense(source: Any, window: str = "2 ms", dirs: int = 8, radius: int = 1, params: dict | None = None) -> EIRGraph
- Dependencies: XYToChannel, multiple ShiftXY, DelayLine, EventFuse.
- Tests: Generate east/north streams; assert corresponding directional channels fire.

3. Vision: corner_harris_events(source, window="5 ms")
- Purpose: event-Harris proxy via orthogonal gradients and coincidence; add NMS.
- Interface: def corner_harris_events(source: Any, window: str = "5 ms", params: dict | None = None) -> EIRGraph
- Dependencies: XYToChannel, ShiftXY (±x, ±y), CoincidenceN (≥3), DelayLine for NMS.
- Tests: Single corner impulse; assert localized response; NMS reduces spread.

4. Vision: event_roi_segmenter(source, window="10 ms", min_area=5)
- Purpose: simple segmentation using time surface threshold + clustering proxy.
- Interface: def event_roi_segmenter(source: Any, window: str = "10 ms", min_area: int = 5, params: dict | None = None) -> EIRGraph
- Dependencies: TimeSurface (ExpDecay), threshold gate (AdaptiveThreshold), optional Cluster2D.
- Tests: Two clusters; assert two ROI event outputs.

5. Audio: gcc_phat_localization(mic_pair, n_fft=256, hop="5 ms")
- Purpose: DOA via GCC-PHAT proxy (phase transform cross-correlation peaks).
- Interface: def gcc_phat_localization(mic_pair: Any, n_fft: int = 256, hop: str = "5 ms", params: dict | None = None) -> EIRGraph
- Dependencies: STFT (per channel), CrossCorr/GCCPHAT proposed op, EventFuse for peak gating.
- Tests: Two-channel synthetic delay; assert correct TDOA peak; golden trace.

6. Audio: onset_detector(stream, n_fft=256, hop="5 ms")
- Purpose: detect transient onsets in audio.
- Interface: def onset_detector(stream: Any, n_fft: int = 256, hop: str = "5 ms", params: dict | None = None) -> EIRGraph
- Dependencies: STFT, MelBands optional, AdaptiveThreshold for energy delta.
- Tests: Synthetic note onsets; assert detection within tolerance.

7. Audio: diarization_multi(mic_source, window="2 s")
- Purpose: multi-speaker segmentation with overlapping talk detection proxy.
- Interface: def diarization_multi(mic_source: Any, window: str = "2 s", params: dict | None = None) -> EIRGraph
- Dependencies: MelBands, CoincidenceN, sliding aggregation.
- Tests: Two alternating tone bands; assert alternating segments.

8. Robotics: event_odometry_1d(xy_source, window="5 ms")
- Purpose: estimate motion magnitude via directional flow difference.
- Interface: def event_odometry_1d(xy_source: Any, window: str = "5 ms", params: dict | None = None) -> EIRGraph
- Dependencies: optical_flow_dense (reuse), aggregation of E/W to velocity proxy.
- Tests: East-moving stream; assert positive velocity proxy.

9. Robotics: obstacle_avoidance(xy_source, tau="10 ms", v_th=0.5)
- Purpose: reflex-based avoidance using local activity → LIF threshold.
- Interface: def obstacle_avoidance(xy_source: Any, tau: str = "10 ms", v_th: float = 0.5, params: dict | None = None) -> EIRGraph
- Dependencies: XYToChannel, window reduction (WindowReduceEvents), LIFNeuron.
- Tests: Burst in front region; assert reflex spike.

10. Timeseries: anomaly_ewma(stream, tau="100 ms", z=3.0)
- Purpose: EWMA-based anomaly detection; event spikes when deviations exceed z.
- Interface: def anomaly_ewma(stream: Any, tau: str = "100 ms", z: float = 3.0, params: dict | None = None) -> EIRGraph
- Dependencies: AdaptiveThreshold-like op (proposed), LIFNeuron.
- Tests: Step change; assert detection; silence baseline → no triggers.

11. Timeseries: online_change_point_bayesian(stream, window="500 ms")
- Purpose: BOCPD-like proxy using multiple delays and fuses.
- Interface: def online_change_point_bayesian(stream: Any, window: str = "500 ms", params: dict | None = None) -> EIRGraph
- Dependencies: DelayLine lattice, EventFuse multi-threshold (CoincidenceN).
- Tests: Two change points; assert two outputs.

12. Wellness: hrv_rr_detector(beat_stream, min_rr_ms=300)
- Purpose: detect RR intervals and derive HRV metrics.
- Interface: def hrv_rr_detector(beat_stream: Any, min_rr_ms: int = 300, params: dict | None = None) -> EIRGraph
- Dependencies: IntervalEstimator (proposed) generating inter-event intervals, EventFuse for artifacts.
- Tests: Synthetic beats with known RR; assert intervals and HRV index outputs.

8) Testing strategies (for new and existing modules)
- Synthetic stream generators mirroring current tests:
  - Audio: [sine_pcm()](eventflow-modules/tests/test_audio_modules.py:6)
  - Vision: [dvs_stream_east()](eventflow-modules/tests/test_domain_modules.py:11), [dvs_single()](eventflow-modules/tests/test_domain_modules.py:19)
  - Generic: [impulses()](eventflow-modules/tests/test_domain_modules.py:23)
- Golden traces per module and conformance checks using [compare_traces_jsonl()](eventflow-core/conformance/comparator.py:60)
- Negative/pathological cases: zero events, burst rates, mismatched window/delay, extremely large/small params, long durations.
- Determinism: run twice with same seed and inputs; bit-exact trace equality.

9) Documentation plan
- Expand eventflow-modules/README.md with module catalog, per-module short docs, and examples.
- Add per-module docstrings detailing:
  - Inputs (expected dims/units and required node names), outputs, parameter defaults and types, suggested ranges.
  - Integration examples with SAL JSONL traces via ef CLI (sal-stream → run).
- Provide a modules quickstart similar to PRE_RELEASE_GUIDE, including import guidance and example code.

10) Integration and packaging guidelines
- Keep modules strictly EIRGraph builders (no SAL device code).
- Publish pretrained graphs to the model hub and package EFPKG manifests with versioned compatibility.
- Ensure module public APIs adhere to SemVer; expose stable entry points from eventflow_modules.<domain>.<func>.

Summary of actionable next steps
- Add docstrings/validation across existing module functions: e.g., [voice_activity()](eventflow-modules/eventflow_modules/audio/vad.py:6), [optical_flow()](eventflow-modules/eventflow_modules/vision/optical_flow.py:6), [event_slam()](eventflow-modules/eventflow_modules/robotics/slam.py:6), [change_point()](eventflow-modules/eventflow_modules/timeseries/change_point.py:6) etc.
- Add golden-trace tests for one representative in each domain.
- Implement optical_flow_dense (no new core ops needed).
- Draft TimeSurface op in core to enable time_surface and roi_segmenter modules.
- Design AdaptiveThreshold, IntervalEstimator ops and add to core ops backlog.

This analysis provides a targeted enhancement plan for current modules and a concrete roadmap for the next 12 modules that expand EventFlow’s capabilities across vision, audio, robotics, time series, and wellness, while remaining compatible with SAL/Core abstractions and deterministic execution.