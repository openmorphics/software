EventFlow System User Stories (Consolidated, code-traceable)

Note on traceability and links:
- Each story references concrete code constructs with clickable links. Function/class links include a line number, e.g., [`keyword_spotter()`](eventflow-modules/eventflow_modules/audio/kws.py:6); file links omit a line number, e.g., [`audio/__init__.py`](eventflow-modules/eventflow_modules/audio/__init__.py).

Module: eventflow-modules — Audio
Title: Build audio analysis graphs (VAD, KWS, Diarization, Localization) with deterministic frontends

As an application ML engineer,
I want ready-to-use audio graph builders for voice activity, keyword spotting, diarization, localization, and feature frontends,
So that I can assemble production-ready event-processing pipelines without hand-wiring DSP and neuron ops.

Acceptance Criteria:
- I can import the audio module entry points from [`audio/__init__.py`](eventflow-modules/eventflow_modules/audio/__init__.py) which re-export builders for VAD, KWS, diarization, localization, and frontends.
- Voice Activity Detection:
  - Calling [`voice_activity()`](eventflow-modules/eventflow_modules/audio/vad.py:6) returns an [`EIRGraph`](eventflow-core/eventflow_core/eir/graph.py:17) with nodes: [`STFT`](eventflow-core/eventflow_core/eir/ops.py:54) → [`MelBands`](eventflow-core/eventflow_core/eir/ops.py:63) → [`EventFuse`](eventflow-core/eventflow_core/eir/ops.py:25).
  - Graph connections follow [`connect()`](eventflow-core/eventflow_core/eir/graph.py:23), with mel features split across EventFuse ports per [`voice_activity()`](eventflow-modules/eventflow_modules/audio/vad.py:26).
- Keyword Spotting:
  - Calling [`keyword_spotter()`](eventflow-modules/eventflow_modules/audio/kws.py:6) builds STFT → Mel → [`LIFNeuron`](eventflow-core/eventflow_core/eir/ops.py:10) and wires ports as in [`keyword_spotter()`](eventflow-modules/eventflow_modules/audio/kws.py:27).
- Speaker Diarization:
  - Calling [`diarization()`](eventflow-modules/eventflow_modules/audio/diarization.py:6) builds STFT → Mel → EventFuse (activity bursts) with connections per [`diarization()`](eventflow-modules/eventflow_modules/audio/diarization.py:26).
- Sound Localization:
  - Calling [`localization()`](eventflow-modules/eventflow_modules/audio/localization.py:6) builds STFT → Mel → EventFuse and wires mel streams to both fuse inputs per [`localization()`](eventflow-modules/eventflow_modules/audio/localization.py:26).
- Feature Frontends:
  - Calling [`stft_frontend()`](eventflow-modules/eventflow_modules/audio/frontend.py:6) creates a single STFT node per [`add_node()`](eventflow-core/eventflow_core/eir/graph.py:22).
  - Calling [`mel_frontend()`](eventflow-modules/eventflow_modules/audio/frontend.py:22) creates STFT→Mel with connections per [`mel_frontend()`](eventflow-modules/eventflow_modules/audio/frontend.py:39).
- All builders accept time-like strings (e.g., "10 ms") that are later normalized via [`time_to_ns()`](eventflow-core/eventflow_core/eir/types.py:20) when executing with the runtime scheduler [`build_exec_nodes()`](eventflow-core/eventflow_core/runtime/scheduler.py:18).
- The resulting graphs can be executed using [`run_event_mode()`](eventflow-core/eventflow_core/runtime/exec.py:7) and serialized using [`save()`](eventflow-core/eventflow_core/eir/serialize.py:5)/[`load()`](eventflow-core/eventflow_core/eir/serialize.py:10).

Edge Cases and Considerations:
- Error scenarios:
  - Providing parameters that cause a graph cycle raises "cycle detected" from [`EIRGraph.topo()`](eventflow-core/eventflow_core/eir/graph.py:34).
  - Invalid time strings raise from [`parse_time()`](eventflow-core/eventflow_core/util/units.py:10).
- Data validation: STFT/Mel parameters are forwarded to ops; semantic checks occur in runtime build via [`build_exec_nodes()`](eventflow-core/eventflow_core/runtime/scheduler.py:50)/[`build_mel_filters()`](eventflow-core/eventflow_core/eir/ops.py:131).
- Performance: Deterministic software ops (STFT, Mel, LIF) provide reproducible behavior.

Module: eventflow-modules — Vision
Title: Detect motion, track objects, and find corners from event-camera streams

As a computer vision engineer,
I want graph templates for optical flow, corner detection, gesture detection, and object tracking,
So that I can rapidly prototype event-camera applications.

Acceptance Criteria:
- I can import vision builders from [`vision/__init__.py`](eventflow-modules/eventflow_modules/vision/__init__.py).
- Optical Flow:
  - Calling [`optical_flow()`](eventflow-modules/eventflow_modules/vision/optical_flow.py:6) maps events via [`XYToChannel`](eventflow-core/eventflow_core/eir/ops.py:186), shifts via [`ShiftXY`](eventflow-core/eventflow_core/eir/ops.py:194), aligns with [`DelayLine`](eventflow-core/eventflow_core/eir/ops.py:20), and detects coincidences with [`EventFuse`](eventflow-core/eventflow_core/eir/ops.py:25) per connections at [`optical_flow()`](eventflow-modules/eventflow_modules/vision/optical_flow.py:38).
- Corner Tracking:
  - Calling [`corner_tracking()`](eventflow-modules/eventflow_modules/vision/corner_tracking.py:6) computes coincidence between orthogonal spatial shifts using EventFuse as in [`corner_tracking()`](eventflow-modules/eventflow_modules/vision/corner_tracking.py:25).
- Object Tracking:
  - Calling [`object_tracking()`](eventflow-modules/eventflow_modules/vision/object_tracking.py:6) performs self-coincidence across a short delay per [`object_tracking()`](eventflow-modules/eventflow_modules/vision/object_tracking.py:23).
- Gesture Detection:
  - Calling [`gesture_detect()`](eventflow-modules/eventflow_modules/vision/gesture_detect.py:5) configures an EventFuse window over an upstream flow or source graph.
- All functions return [`EIRGraph`](eventflow-core/eventflow_core/eir/graph.py:17) executable via [`run_event_mode()`](eventflow-core/eventflow_core/runtime/exec.py:7).

Edge Cases and Considerations:
- Spatial bounds are clipped per [`step_shift_xy()`](eventflow-core/eventflow_core/eir/ops.py:213) and [`step_xy_to_ch()`](eventflow-core/eventflow_core/eir/ops.py:203).
- Width/height defaults must match sensor dimensions.
- Time window strings parse via [`time_to_ns()`](eventflow-core/eventflow_core/eir/types.py:20).

Module: eventflow-modules — Robotics
Title: Event-driven robotics templates: reflexes, obstacle avoidance, and SLAM fusion

As a robotics engineer,
I want prebuilt event-graph templates for reflex control, obstacle detection, and DVS+IMU fusion,
So that I can bootstrap robot pipelines that respond in real time.

Acceptance Criteria:
- I can import robotics builders from [`robotics/__init__.py`](eventflow-modules/eventflow_modules/robotics/__init__.py).
- Reflex control:
  - Calling [`reflex_controller()`](eventflow-modules/eventflow_modules/robotics/reflex.py:5) creates a [`LIFNeuron`](eventflow-core/eventflow_core/eir/ops.py:10) node for fast thresholding.
- Obstacle avoidance:
  - Calling [`obstacle_avoidance()`](eventflow-modules/eventflow_modules/robotics/obstacle.py:6) wires an [`EventFuse`](eventflow-core/eventflow_core/eir/ops.py:25) window to detect dense activity.
- Event SLAM fusion:
  - Calling [`event_slam()`](eventflow-modules/eventflow_modules/robotics/slam.py:6) maps DVS via [`XYToChannel`](eventflow-core/eventflow_core/eir/ops.py:186), aligns IMU with [`DelayLine`](eventflow-core/eventflow_core/eir/ops.py:20), and fuses signals via [`EventFuse`](eventflow-core/eventflow_core/eir/ops.py:25) per connections at [`event_slam()`](eventflow-modules/eventflow_modules/robotics/slam.py:32).

Edge Cases:
- Window lengths and min_count tune sensitivity.
- IMU delay alignment set at [`event_slam()`](eventflow-modules/eventflow_modules/robotics/slam.py:22).

Module: eventflow-modules — Timeseries
Title: Event-based timeseries analytics: anomaly, change points, spike patterns

As a data engineer,
I want callable graph builders for timeseries analytics primitives,
So that I can deploy simple analytics without custom DSP.

Acceptance Criteria:
- Import from [`timeseries/__init__.py`](eventflow-modules/eventflow_modules/timeseries/__init__.py).
- Anomaly detection:
  - [`anomaly_detector()`](eventflow-modules/eventflow_modules/timeseries/anomaly.py:5) thresholds via [`LIFNeuron`](eventflow-core/eventflow_core/eir/ops.py:10).
- Change points:
  - [`change_point()`](eventflow-modules/eventflow_modules/timeseries/change_point.py:6) detects self-coincidence using [`DelayLine`](eventflow-core/eventflow_core/eir/ops.py:20) + [`EventFuse`](eventflow-core/eventflow_core/eir/ops.py:25).
- Spike pattern mining:
  - [`spike_pattern_mining()`](eventflow-modules/eventflow_modules/timeseries/spike_mining.py:6) performs self-coincidence with tunable window/min_count.

Edge Cases:
- Window selection impacts sensitivity; time strings via [`time_to_ns()`](eventflow-core/eventflow_core/eir/types.py:20).

Module: eventflow-modules — Wellness
Title: Wellness scaffolds: HRV, sleep staging, stress

As a digital health modeler,
I want wellness-oriented graph templates,
So that I can prototype physiological analytics.

Acceptance Criteria:
- Import from [`wellness/__init__.py`](eventflow-modules/eventflow_modules/wellness/__init__.py).
- HRV:
  - [`hrv_index()`](eventflow-modules/eventflow_modules/wellness/hrv.py:5) uses [`DelayLine`](eventflow-core/eventflow_core/eir/ops.py:20) for HRV windows.
- Sleep staging:
  - [`sleep_staging()`](eventflow-modules/eventflow_modules/wellness/sleep.py:6) periodicity/coincidence with [`EventFuse`](eventflow-core/eventflow_core/eir/ops.py:25).
- Stress index:
  - [`stress_index()`](eventflow-modules/eventflow_modules/wellness/stress.py:6) burst detection over longer windows.

Edge Cases:
- Choose appropriate epoch sizes (e.g., 30 s, 60 s).

Module: eventflow-modules — Creative
Title: Creative event pipelines: graphics, music generation, sequencing

As a creative technologist,
I want creative-focused event graph scaffolds,
So that I can visualize and sonify event streams.

Acceptance Criteria:
- Import from [`creative/__init__.py`](eventflow-modules/eventflow_modules/creative/__init__.py).
- Graphics:
  - [`event_graphics()`](eventflow-modules/eventflow_modules/creative/graphics.py:6) provides an identity delay via [`DelayLine`](eventflow-core/eventflow_core/eir/ops.py:20).
- Bio sequencer:
  - [`bio_sequencer()`](eventflow-modules/eventflow_modules/creative/sequencer.py:6) aligns inputs via [`DelayLine`](eventflow-core/eventflow_core/eir/ops.py:20) and coincidence via [`EventFuse`](eventflow-core/eventflow_core/eir/ops.py:25).
- Music generator scaffold:
  - [`music_generator()`](eventflow-modules/eventflow_modules/creative/musicgen.py:4) returns a simple, functional [`EIRGraph`](eventflow-core/eventflow_core/eir/graph.py:17) containing a feedback loop with a `DelayLine` and `LIFNeuron`.

Edge Cases:
- The `music_generator` builder provides a foundational graph that can be extended by the user.

Module: eventflow-core (runtime, EIR, ops, validators)
Title: Define, validate, serialize, and execute event graphs deterministically

As a platform engineer,
I want a deterministic core to define ops, validate graphs, and execute them,
So that I can build reproducible pipelines.

Acceptance Criteria:
- Graph model and DAG safety via [`EIRGraph`](eventflow-core/eventflow_core/eir/graph.py:17), [`add_node()`](eventflow-core/eventflow_core/eir/graph.py:22), [`connect()`](eventflow-core/eventflow_core/eir/graph.py:23), and cycle detection in [`topo()`](eventflow-core/eventflow_core/eir/graph.py:34).
- Operators:
  - Neuron/synapse: [`LIFNeuron`](eventflow-core/eventflow_core/eir/ops.py:10), [`ExpSynapse`](eventflow-core/eventflow_core/eir/ops.py:15).
  - Stream ops: [`DelayLine`](eventflow-core/eventflow_core/eir/ops.py:20), [`EventFuse`](eventflow-core/eventflow_core/eir/ops.py:25).
  - Audio ops: [`STFT`](eventflow-core/eventflow_core/eir/ops.py:54)/[`step_stft()`](eventflow-core/eventflow_core/eir/ops.py:83), [`MelBands`](eventflow-core/eventflow_core/eir/ops.py:63)/[`step_mel()`](eventflow-core/eventflow_core/eir/ops.py:156), [`build_mel_filters()`](eventflow-core/eventflow_core/eir/ops.py:131).
  - Vision ops: [`XYToChannel`](eventflow-core/eventflow_core/eir/ops.py:186)/[`step_xy_to_ch()`](eventflow-core/eventflow_core/eir/ops.py:203), [`ShiftXY`](eventflow-core/eventflow_core/eir/ops.py:194)/[`step_shift_xy()`](eventflow-core/eventflow_core/eir/ops.py:213).
- Types/time: [`Port`](eventflow-core/eventflow_core/eir/types.py:7), [`OpDef`](eventflow-core/eventflow_core/eir/types.py:13), [`time_to_ns()`](eventflow-core/eventflow_core/eir/types.py:20)/[`parse_time()`](eventflow-core/eventflow_core/util/units.py:10).
- Runtime execution: [`run_event_mode()`](eventflow-core/eventflow_core/runtime/exec.py:7), [`run_fixed_dt()`](eventflow-core/eventflow_core/runtime/exec.py:29); scheduler [`build_exec_nodes()`](eventflow-core/eventflow_core/runtime/scheduler.py:18).
- Serialization/tracing: [`save()`](eventflow-core/eventflow_core/eir/serialize.py:5), [`load()`](eventflow-core/eventflow_core/eir/serialize.py:10); trace [`record()`](eventflow-core/eventflow_core/runtime/trace.py:3), [`load()`](eventflow-core/eventflow_core/runtime/trace.py:4).
- Validators/conformance: [`validate_eir()`](eventflow-core/validators.py:521), [`validate_event_tensor_json()`](eventflow-core/validators.py:558), [`validate_event_tensor_jsonl_path()`](eventflow-core/validators.py:583), [`validate_dcd()`](eventflow-core/validators.py:655), [`validate_efpkg()`](eventflow-core/validators.py:676), trace comparator [`trace_equivalent()`](eventflow-core/eventflow_core/conformance/compare.py:2).
- Package exports: [`eventflow_core/__init__.py`](eventflow-core/eventflow_core/__init__.py), and namespace init stubs: [`eir/__init__.py`](eventflow-core/eventflow_core/eir/__init__.py), [`runtime/__init__.py`](eventflow-core/eventflow_core/runtime/__init__.py), [`compiler/__init__.py`](eventflow-core/eventflow_core/compiler/__init__.py), [`util/__init__.py`](eventflow-core/eventflow_core/util/__init__.py), [`conformance/__init__.py`](eventflow-core/eventflow_core/conformance/__init__.py), [`simulator/__init__.py`](eventflow-core/eventflow_core/simulator/__init__.py).

Edge Cases and Considerations:
- Determinism: LIF refractory handling in [`step_lif()`](eventflow-core/eventflow_core/eir/ops.py:47).
- Missing/invalid params surface during node exec construction in [`build_exec_nodes()`](eventflow-core/eventflow_core/runtime/scheduler.py:21).
- Version compatibility warnings in validators (e.g., [`validate_eir()`](eventflow-core/validators.py:526)).

Module: eventflow-sal (Sensor Abstraction Layer)
Title: Normalize sensor streams to Event Tensor JSONL and open device/file sources

As a data ingestion engineer,
I want to open device/file URIs and normalize them to Event Tensor JSONL,
So that models and simulators consume consistent event data.

Acceptance Criteria:
- High-level streaming API:
  - [`stream_to_jsonl()`](eventflow-sal/api.py:192) normalizes SAL sources; parses URIs via [`parse_sensor_uri()`](eventflow-sal/eventflow_sal/api/uri.py:7); writes header via [`_write_header()`](eventflow-sal/api.py:45) and events via [`_write_event()`](eventflow-sal/api.py:57); pass-through handled by [`_normalize_existing_jsonl()`](eventflow-sal/api.py:85).
- Opening sources:
  - Wrapper [`open()`](eventflow-sal/__init__.py:13) delegates to [`open()`](eventflow-sal/eventflow_sal/open.py:5) which resolves via registry [`resolve_source()`](eventflow-sal/eventflow_sal/registry.py:19) and path resolution [`_effective_path()`](eventflow-sal/eventflow_sal/registry.py:10).
- Drivers:
  - Audio: [`MicSource`](eventflow-sal/eventflow_sal/drivers/audio.py:6) (live unimplemented), [`WAVFileSource`](eventflow-sal/eventflow_sal/drivers/audio.py:13) emits bands via [`audio_band_event()`](eventflow-sal/eventflow_sal/api/packet.py:14).
  - Vision/DVS: [`DVSSource`](eventflow-sal/eventflow_sal/drivers/dvs.py:6) (live unimplemented), [`AEDAT4FileSource`](eventflow-sal/eventflow_sal/drivers/dvs.py:13) emits via [`dvs_event()`](eventflow-sal/eventflow_sal/api/packet.py:13) with clock correction [`ClockSync.correct_ns()`](eventflow-sal/eventflow_sal/sync/clock.py:18).
  - IMU: [`IMUSource`](eventflow-sal/eventflow_sal/drivers/imu.py:5) (live unimplemented), [`CSVFileSource`](eventflow-sal/eventflow_sal/drivers/imu.py:12) yields axes via [`imu_axis_event()`](eventflow-sal/eventflow_sal/api/packet.py:15).
- Interfaces/utilities:
  - Sources: [`BaseSource`](eventflow-sal/eventflow_sal/api/source.py:6), [`Replayable`](eventflow-sal/eventflow_sal/api/source.py:14).
  - Packets: [`EventPacket`](eventflow-sal/eventflow_sal/api/packet.py:9).
  - Calibration: [`CalibrationStage`](eventflow-sal/eventflow_sal/calib/base.py:2), [`DeadPixelMask`](eventflow-sal/eventflow_sal/calib/dvs.py:6), [`PolarityBalance`](eventflow-sal/eventflow_sal/calib/dvs.py:15).
  - Clock & watermark: [`ClockModel`](eventflow-sal/eventflow_sal/sync/clock.py:5), [`ClockSync`](eventflow-sal/eventflow_sal/sync/clock.py:10), [`Watermark`](eventflow-sal/eventflow_sal/sync/watermark.py:1).
  - Misc: [`RateLimiter`](eventflow-sal/eventflow_sal/util/rate.py:2), [`RingBuffer`](eventflow-sal/eventflow_sal/util/ring.py:2).
  - DCD helpers: [`DeviceCapabilityDescriptor`](eventflow-sal/eventflow_sal/api/dcd.py:6), [`validate_dcd()`](eventflow-sal/eventflow_sal/api/dcd.py:12).
- Package structure exports for import stability: [`api/__init__.py`](eventflow-sal/eventflow_sal/api/__init__.py), [`drivers/__init__.py`](eventflow-sal/eventflow_sal/drivers/__init__.py), [`calib/__init__.py`](eventflow-sal/eventflow_sal/calib/__init__.py), [`sync/__init__.py`](eventflow-sal/eventflow_sal/sync/__init__.py), [`eventflow_sal/__init__.py`](eventflow-sal/eventflow_sal/__init__.py). Note: formats/__init__.py removed.

Edge Cases and Considerations:
- Unsupported live devices raise explicitly in [`MicSource.subscribe()`](eventflow-sal/eventflow_sal/drivers/audio.py:11), [`DVSSource.subscribe()`](eventflow-sal/eventflow_sal/drivers/dvs.py:11), [`IMUSource.subscribe()`](eventflow-sal/eventflow_sal/drivers/imu.py:10).
- Registry rejects JSONL in [`resolve_source()`](eventflow-sal/eventflow_sal/registry.py:33); use [`stream_to_jsonl()`](eventflow-sal/api.py:192).
- Wrapper [`read()`](eventflow-sal/__init__.py:19) validates presence of `subscribe()`.
- Integration: CLI [`cmd_sal_stream()`](eventflow-cli/ef.py:263) invokes SAL [`stream_to_jsonl()`](eventflow-sal/api.py:192).

Module: eventflow-backends (registry, CPU/GPU simulators)
Title: Plan and execute EIR graphs on simulated backends with deterministic traces

As a deployment engineer,
I want backend planning and execution with canonical, deterministic traces,
So that I can generate golden traces and validate models.

Acceptance Criteria:
- Backend discovery/facades:
  - [`list_backends()`](eventflow-backends/__init__.py:10), [`get_backend()`](eventflow-backends/__init__.py:18).
  - In-process mini-registry [`get_backend()`](eventflow-backends/eventflow_backends/__init__.py:20).
  - Dynamic registry: [`list_backends()`](eventflow-backends/registry/registry.py:151), [`load_backend()`](eventflow-backends/registry/registry.py:155).
- Backend interface:
  - [`DeviceCapabilityDescriptor`](eventflow-backends/eventflow_backends/api.py:8), [`Backend`](eventflow-backends/eventflow_backends/api.py:17) with [`compile()`](eventflow-backends/eventflow_backends/api.py:25)/[`run_graph()`](eventflow-backends/eventflow_backends/api.py:28).
- CPU-sim (in-process) backend:
  - [`CPUSimBackend`](eventflow-backends/eventflow_backends/cpu_sim/backend.py:15) compiles via [`compile()`](eventflow-backends/eventflow_backends/cpu_sim/backend.py:22) and executes graphs by delegating to core [`run_event_mode()`](eventflow-core/eventflow_core/runtime/exec.py:7) in [`run_graph()`](eventflow-backends/eventflow_backends/cpu_sim/backend.py:25).
- Registry CPU/GPU simulators:
  - CPU: [`plan_cpu_sim()`](eventflow-backends/cpu_sim/executor.py:44), [`run_cpu_sim()`](eventflow-backends/cpu_sim/executor.py:188).
  - GPU: [`plan_gpu_sim()`](eventflow-backends/gpu_sim/executor.py:42), [`run_gpu_sim()`](eventflow-backends/gpu_sim/executor.py:183).
  - DCD load in constructors: [`CpuSimBackend`](eventflow-backends/registry/registry.py:56), [`GpuSimBackend`](eventflow-backends/registry/registry.py:105).
- Integration with CLI:
  - Planning via [`cmd_build()`](eventflow-cli/ef.py:503) and run via [`cmd_run()`](eventflow-cli/ef.py:534) using registry [`load_backend()`](eventflow-backends/registry/registry.py:155).

Edge Cases and Considerations:
- Missing DCD files raise in registry constructors (e.g., [`cpu-sim`](eventflow-backends/registry/registry.py:60)).
- EIR validation errors fail planning early in [`plan()`](eventflow-backends/registry/registry.py:80/129).
- Unknown backend names raise in [`get_backend()`](eventflow-backends/__init__.py:35) and [`load_backend()`](eventflow-backends/registry/registry.py:160).
- Backend registry provides in-process simulators; top-level stub __init__.py files have been removed. See [`eventflow_backends/__init__.py`](eventflow-backends/eventflow_backends/__init__.py:15) and dynamic registry [`list_backends()`](eventflow-backends/registry/registry.py:154), [`load_backend()`](eventflow-backends/registry/registry.py:158).

Module: eventflow-hub (Local packaging and registry)
Title: Package and manage model artifacts locally (hub stubs)

As an MLOps engineer,
I want to package model artifacts and manage them in a local registry,
So that I can version models and fetch bundles for deployment.

Acceptance Criteria:
- Client API:
  - [`HubClient`](eventflow-hub/eventflow_hub/client.py:6) uses [`LocalRegistry`](eventflow-hub/eventflow_hub/registry.py:7); remote methods raise [`HubError`](eventflow-hub/eventflow_hub/errors.py:2).
- Local filesystem registry:
  - Add/get/list via [`add()`](eventflow-hub/eventflow_hub/registry.py:27), [`get()`](eventflow-hub/eventflow_hub/registry.py:35), [`list()`](eventflow-hub/eventflow_hub/registry.py:45).
- Packaging:
  - Bundle via [`pack_bundle()`](eventflow-hub/eventflow_hub/pack.py:6); unpack via [`unpack_bundle()`](eventflow-hub/eventflow_hub/pack.py:21).
- Metadata schemas:
  - [`ModelCard`](eventflow-hub/eventflow_hub/schemas.py:6), [`CapManifest`](eventflow-hub/eventflow_hub/schemas.py:15), [`TraceMeta`](eventflow-hub/eventflow_hub/schemas.py:21).
- Token handling:
  - [`TokenProvider`](eventflow-hub/eventflow_hub/auth.py:3).

Edge Cases and Considerations:
- Missing required files cause [`pack_bundle()`](eventflow-hub/eventflow_hub/pack.py:11) to raise.
- Remote methods not implemented: [`push_remote()`](eventflow-hub/eventflow_hub/client.py:26), [`pull_remote()`](eventflow-hub/eventflow_hub/client.py:29).

Module: eventflow-cli (ef.py and eventflow_cli/*)
Title: Validate, stream, plan, run, compare — full CLI surface for developer operations

As a developer or tester,
I want CLI commands for validation, streaming from SAL, backend planning/execution, profiling, and packaging,
So that I can manage the full lifecycle from data to golden traces.

Acceptance Criteria (ef.py):
- Version/registry:
  - [`cmd_version()`](eventflow-cli/ef.py:168), [`cmd_list_backends()`](eventflow-cli/ef.py:175).
- Validators:
  - [`cmd_validate_eir()`](eventflow-cli/ef.py:192), [`cmd_validate_event()`](eventflow-cli/ef.py:204), [`cmd_validate_dcd()`](eventflow-cli/ef.py:225), [`cmd_validate_efpkg()`](eventflow-cli/ef.py:237), [`cmd_validate_trace()`](eventflow-cli/ef.py:253).
- SAL streaming:
  - [`cmd_sal_stream()`](eventflow-cli/ef.py:263) → SAL [`stream_to_jsonl()`](eventflow-sal/api.py:192).
- Profiling and packaging:
  - [`cmd_profile()`](eventflow-cli/ef.py:288), [`cmd_package()`](eventflow-cli/ef.py:402).
- Planning and execution:
  - [`cmd_build()`](eventflow-cli/ef.py:503), [`cmd_run()`](eventflow-cli/ef.py:534).
- Compare traces:
  - [`cmd_compare_traces()`](eventflow-cli/ef.py:570).
- CLI entrypoint:
  - [`main()`](eventflow-cli/ef.py:588).

Acceptance Criteria (eventflow_cli lightweight CLI):
- Entrypoint and parser: [`make_parser()`](eventflow-cli/eventflow_cli/main.py:4), [`main()`](eventflow-cli/eventflow_cli/main.py:31).
- Subcommands:
  - Build: [`handle()`](eventflow-cli/eventflow_cli/build.py:4).
  - Run: [`handle()`](eventflow-cli/eventflow_cli/run.py:4).
  - Profile: [`handle()`](eventflow-cli/eventflow_cli/profile.py:4).
  - Validate: [`handle()`](eventflow-cli/eventflow_cli/validate.py:4).

Module: eventflow-modules (root aggregator)
Title: Domain module aggregator for audio/vision/robotics/timeseries/wellness/creative

As a library consumer,
I want a single namespace that exposes domain-specific module groups,
So that I can discover and import domain builders efficiently.

Acceptance Criteria:
- Root exposes domain namespaces via [`eventflow_modules/__init__.py`](eventflow-modules/eventflow_modules/__init__.py) and each submodule’s `__init__` re-exports primary builders:
  - Audio: [`audio/__init__.py`](eventflow-modules/eventflow_modules/audio/__init__.py)
  - Vision: [`vision/__init__.py`](eventflow-modules/eventflow_modules/vision/__init__.py)
  - Robotics: [`robotics/__init__.py`](eventflow-modules/eventflow_modules/robotics/__init__.py)
  - Timeseries: [`timeseries/__init__.py`](eventflow-modules/eventflow_modules/timeseries/__init__.py)
  - Wellness: [`wellness/__init__.py`](eventflow-modules/eventflow_modules/wellness/__init__.py)
  - Creative: [`creative/__init__.py`](eventflow-modules/eventflow_modules/creative/__init__.py)

System-level End-to-End Workflow (from user input to backend output):
- Normalize input using ef CLI SAL command [`cmd_sal_stream()`](eventflow-cli/ef.py:263) → SAL [`stream_to_jsonl()`](eventflow-sal/api.py:192) → drivers via registry [`resolve_source()`](eventflow-sal/eventflow_sal/registry.py:19).
- Construct an EIR graph using builders (e.g., [`keyword_spotter()`](eventflow-modules/eventflow_modules/audio/kws.py:6)) returning [`EIRGraph`](eventflow-core/eventflow_core/eir/graph.py:17).
- Validate/serialize via core validators [`validate_eir()`](eventflow-core/validators.py:521) and EIR IO [`save()`](eventflow-core/eventflow_core/eir/serialize.py:5)/[`load()`](eventflow-core/eventflow_core/eir/serialize.py:10).
- Plan/execute via ef CLI [`cmd_build()`](eventflow-cli/ef.py:503)/[`cmd_run()`](eventflow-cli/ef.py:534) using registry [`load_backend()`](eventflow-backends/registry/registry.py:155), generating golden traces via [`run_cpu_sim()`](eventflow-backends/cpu_sim/executor.py:188) or [`run_gpu_sim()`](eventflow-backends/gpu_sim/executor.py:183).
- Conformance via ef CLI [`cmd_compare_traces()`](eventflow-cli/ef.py:570) → comparator [`trace_equivalent()`](eventflow-core/eventflow_core/conformance/compare.py:2).
- Packaging via ef CLI [`cmd_package()`](eventflow-cli/ef.py:402) validated by core [`validate_efpkg()`](eventflow-core/validators.py:676); archive via hub [`pack_bundle()`](eventflow-hub/eventflow_hub/pack.py:6) and store in local hub [`add()`](eventflow-hub/eventflow_hub/registry.py:27).

Coverage Confirmation:
- eventflow-modules: all builders and __init__.py files for audio, vision, robotics, timeseries, wellness, creative are referenced.
- eventflow-core: graph, ops, types, serialize, validate, runtime (exec/scheduler/trace), validators, conformance compare, and namespace init stubs.
- eventflow-sal: top-level wrapper, high-level API, open/registry, api/* (source, uri, packet, dcd), calib/*, drivers/*, sync/*, util/*, and stubs.
- eventflow-backends: façade, in-process registry, backend API, cpu_sim backend and executor, gpu_sim executor, dynamic registry; package stubs.
- eventflow-hub: client, registry, pack, schemas, auth, errors.
- eventflow-cli: ef.py commands and lightweight eventflow_cli handlers and parser.