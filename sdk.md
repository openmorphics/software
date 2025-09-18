EventFlow: A Hardware- and Sensor‑Agnostic Event Computing SDK

Overview: We propose EventFlow, a unified SDK that lets developers write one event‑driven application and run it on any neuromorphic chip or event sensor with deterministic behavior. Drawing on lessons from mainstream AI (e.g. PyTorch) and emerging neuromorphic standards, EventFlow features a layered architecture with a common Event Intermediate Representation (EIR), a Sensor Abstraction Layer (SAL), and modular hardware backends. Applications are expressed in high-level Python (with C++/gRPC bindings) and rely on unit-checked timing semantics and reproducible simulation. The design emphasizes portability, “late binding” of hardware/sensors, and automated fallbacks so that code runs on existing simulators or CPUs when dedicated hardware is unavailable. This mirrors the vision of the Open Neuromorphic community for hardware-agnostic neuromorphic development
open-neuromorphic.org
open-neuromorphic.org
.

Layered Architecture (Thin Waist)

EventFlow’s software stack has a “thin waist” abstraction (Figure 1). Developers build event graphs with high-level operators; these compile down to a hardware-neutral IR (EIR) and then to device‑specific binaries via backends.

Event Intermediate Representation (EIR): A typed, unit‑aware IR for event programs. EIR represents spike/event streams, neuron/synapse primitives, delays, kernels and stateful operations. It enforces deterministic ordering of events and explicit timing (e.g. timestamps with units like μs or ms). By analogy to the recent Neuromorphic Intermediate Representation (NIR), EIR decouples model definition from hardware specifics
open-neuromorphic.org
. Like PyNN’s high-level API
neuralensemble.org
 or Lava’s Python layers
open-neuromorphic.org
, users write code once; EventFlow’s compiler lowers EIR to each backend. If a target lacks a feature (e.g. certain neuron model), the compiler inserts a software fallback (or simulator) or warns of possible constraints. The EIR module is packaged (e.g. eventflow-core) with definitions of standard ops (LIF neurons, STDP, convolutions, etc.) and an extensible opset schema.

Sensor Abstraction Layer (SAL): Uniform drivers for event‑based sensors. SAL ingests raw streams from devices (DVS cameras, microphones, IMUs, biometric sensors, etc.) and normalizes them into timestamped event packets (t, channel, magnitude, metadata). Standard source types (e.g. vision.dvs, audio.mic, imu.6dof) are defined. For example, a DVS yields events on pixel brightness changes, while a microphone can be time‑encoded into spikes (e.g. via cochlear or AER encoders). SAL enforces synchronized clocks (compensating for drift/jitter) and unit conversion (e.g. converting analog IMU signals to acceleration spikes). In effect, SAL exposes semantic data channels (e.g. “red corner events”, “speech onset events”) instead of vendor APIs. Event-based vision is well‑studied to exploit high dynamic range and low latency
arxiv.org
, and SAL generalizes that pattern to any event or threshold sensor.

Neuromorphic Execution Layer (NEL): A plugin framework of backends. Each backend can target a specific neuromorphic hardware (Intel Loihi/Lava, SpiNNaker, SynSense Speck/Xylo, BrainScaleS, or other ASICs) or a CPU/GPU simulator. Backends declare their capabilities in a JSON schema (neuron models, max neurons/synapses, timing granularity, supported plasticity, energy usage, etc.). At compile time, the EIR-to-hardware mapper matches EIR ops against backend capabilities. This is similar to PyNN’s approach, where a single Python model can run unchanged on multiple simulators and on SpiNNaker/BrainScaleS hardware
neuralensemble.org
. If a target hardware lacks an operation, the compiler either substitutes a coarser version or falls back to CPU simulation (ensuring graceful degradation). For example, Intel’s Lava framework already compiles high‑level networks to run on Loihi or on CPUs
open-neuromorphic.org
; EventFlow generalizes this to multiple vendors. Each backend ensures deterministic execution by logging or seeding randomness; if possible, clocks are synchronized or statically time‑stepped.

Runtime & Tooling: EventFlow includes a runtime scheduler for event queues, buffer management, routing, checkpointing, and hot-swappable pipelines. Developers get tools for visualization (spike rasters, buffer/latency histograms, causal graphs), profiling (latency, power), and debug (trace record/replay). A built‑in simulator supports zero-install development. A compiler front-end converts high-level constructs (or ANN models via surrogate gradients) into EIR; it performs quantization, graph partitioning, and static checks against constraints (e.g. end-to-end latency budgets). A conformance suite runs “golden” inputs through every backend and compares traces (with ε‑bounds)
nature.com
. In short, the tools mirror TensorFlow/PyTorch conveniences (auto diff, serialization, deployment) but for spiking/event graphs
neuralensemble.org
open-neuromorphic.org
.

Figure 1 (below) illustrates the architecture layers (sensor to hardware) and pipeline of a sample event-driven application. The thin-waist EIR ensures any application can flow from SAL through NEL to the chip.

Portability and Determinism

Hardware-Agnostic Portability: EventFlow enforces “write once, run anywhere.” Thanks to the EIR and device capability negotiation, the same codebase can target any registered chip. This is akin to PyTorch’s .to(device) but for neuromorphic devices
open-neuromorphic.org
neuralensemble.org
. If a device lacks a requested feature (say, STDP learning), EventFlow transparently emulates it in software or uses a no‑learning model. The result is maximal reuse of application code: applications bind to abstract “neuromorphic resource sets” rather than specific hardware. Vendors supply thin “driver” plugins that implement the backend interface, so third‑party chips become first-class citizens.

Sensor-Agnostic Portability: By design, applications do not depend on a specific camera/mic/IMU model. SAL drivers calibrate each device and translate to a common event format. For example, all DVS cameras produce (timestamp, x, y, polarity), audio mics produce (timestamp, frequency-band, magnitude), and IMUs (timestamp, axis, acceleration). Applications refer to semantic channels (e.g. “events on channel 0 correspond to red pixels”); SAL maps those to whatever sensor is plugged in. Thus code written for a DAVIS camera works with a Prophesee or iniVation camera alike, and even with recorded AEDAT data files.

Determinism: EventFlow provides two execution modes. In exact event mode, the runtime processes events strictly in timestamp order (breaking ties by defined ordering rules) and all operations are pure functions of past events. This gives a ground‑truth trace. In fixed-step mode, the system discretizes time into Δt steps (chosen per profile), and it tracks errors due to quantization. In either case, the execution is deterministic given a seed: setting RNG seeds yields bitwise-identical spikes (as is already standard in simulators like NEST or Brian). This enables trace replay across runs and platforms, and unit-checked temporal semantics prevent subtle timing bugs.

These guarantees echo the needs identified by neuromorphic researchers. As one community report notes, neuromorphic development is hindered by incompatible APIs and non‑reproducible results
open-neuromorphic.org
open-neuromorphic.org
; hardware‑agnostic IRs and synchronized timing help close that gap. EventFlow’s IR is inspired by NIR and PyNN, which already demonstrate cross-platform reproducibility
open-neuromorphic.org
neuralensemble.org
.

Developer Experience

API: A Python API (import eventflow as ef) is the primary interface, patterned after familiar dataflow/ML libraries. For example, one might write:

cam   = ef.sensors.open("vision.dvs://cam0")         # open any DVS
mic   = ef.sensors.open("audio.mic://default")      # open microphone stream

flow  = ef.vision.optical_flow(cam)                 # high-level event op
gesture = ef.vision.gesture_detect(flow)
kws   = ef.audio.keyword_spotter(mic, phrase="hey event")
fused = ef.fusion.coincidence([gesture, kws], window="50 ms")
ef.compile_and_run(fused, backend="auto", constraints={"latency":"10ms"})


This familiar style (graph construction + compile) is analogous to TensorFlow or PyTorch, but designed for spikes/events. A C++ API and gRPC interface are provided for embedded use.

Batteries-Included Modules: EventFlow includes rich domain libraries (importable as eventflow.vision, eventflow.audio, etc.). For vision: event-native operators like optical flow, corner tracking, object tracking, gesture kernels. For audio: spike-based VAD, keyword spotting, sound localization. Robotics: spiking SLAM primitives, reflex controllers. Time-series: anomaly detectors, change-point sensors. Wellness: HRV stress detectors from heartbeat spikes, sleep event segmentation. Creative: biosignal-driven sequencers, event-reactive graphics. These modules come with pre-trained SNN kernels and demo scripts. (Open-source spiking libraries already show success in many tasks
open-neuromorphic.org
arxiv.org
; EventFlow packages them with unit tests and sample traces.)

Tools: A CLI (ef build, ef run, ef profile, ef validate) wraps common workflows. For debugging, EventFlow provides a web dashboard with spike rasters, spike-time “causal cones” for tracing event influence, buffer occupancies and latency/power histograms. Simulation can be accelerated on GPU via frameworks like snnTorch or Lava’s simulator to speed offline testing
open-neuromorphic.org
open-neuromorphic.org
.

Model & Benchmark Hub: The eventflow-hub (analogous to Hugging Face) hosts a model zoo of EIR modules: vision nets, audio nets, sensor fusion pipelines. Each model is versioned with a capability manifest and golden trace for conformance. Community sharing is encouraged, and conformance badges (passed on hardware) build trust.

Conformance & Quality Assurance

To be a true standard, EventFlow includes rigorous testing. A Trace Equivalence Suite runs reference inputs (e.g. prerecorded DVS or audio clips) on each backend, then compares output event streams to the golden reference (allowing small ε‑bounds for quantization). Benchmarks measure P50/P99 latencies, energy-per-event, and dropped-event rates on each platform. This echoes recent efforts (e.g. NeuroBench) to define objective neuromorphic benchmarks
nature.com
. EventFlow also includes security and safety features: all kernels run sandboxed (no arbitrary code execution), sensor inputs are rate-limited, and sanity checks (e.g. overflow protection, sensor spoofing detection) are built in.

Packaging and Module Breakdown

EventFlow is organized into modular packages for flexibility:

eventflow-core: Core IR definitions, compiler, runtime scheduler and simulator.

eventflow-sal: Sensor drivers and sync/calibration code.

eventflow-backends-*: Each vendor/plugin lives in its own package (e.g. -lava, -spinnaker2, -snipsense, -brainscales). They implement the NEL interface and bundle device DCDs.

eventflow-modules-vision/audio/robotics/...: Domain libraries with EIR component graphs and pretrained weights.

eventflow-cli: Command-line tools for building, running, profiling, packaging apps.

eventflow-hub: The (possibly web-hosted) index of shared EIR models and data.

All code is open-core: core, SAL, simulator, and BASE/REALTIME modules are under a permissive license. Enterprise offerings (optimized backends, advanced quantizers, support) may be commercial.

The repository might have this structure:

eventflow/                  # main repo
├── eventflow-core/         # EIR, compiler, simulator
│   ├── eir/                # IR schemas and ops
│   ├── compiler/           # lowers EIR to backends
│   └── runtime/            # scheduler, checkpointer, etc.
├── eventflow-sal/          # sensor interface and data normalization
│   ├── drivers/            # DVS, audio, IMU, etc. drivers
│   └── sync/               # clock sync and calibration tools
├── eventflow-backends/     # interface specs + vendor plugins
│   ├── lava/
│   ├── spinnaker2/
│   ├── synsense/
│   ├── brainscales/
│   └── cpu_sim/            # default CPU/GPU simulator
├── eventflow-modules/
│   ├── vision/             # optical flow, tracking, gesture
│   ├── audio/              # VAD, KWS, localization
│   ├── robotics/           # reflexes, SLAM primitives
│   ├── timeseries/         # anomaly detection, pattern mining
│   ├── wellness/           # HRV, sleep segmentation
│   └── creative/           # sequencers, generative art
├── eventflow-cli/          # CLI entrypoints
└── eventflow-hub/          # model zoo (may be separate)


Each module includes tests and example applications (e.g. ef.apps.wakeword, motion_cam, stresswatch). By bundling demos (wake-word KWS, drone navigation, spam filter, stress monitor), EventFlow lowers the barrier so developers see immediate value on common tasks.

Technical Specifications

Event Tensor: The primitive data type is a sparse event tensor (list of events with timestamps). All tensors carry units (time, voltage, etc.) to avoid mix-ups. Under the hood this is a compact (timestamp, index, value) format with efficient stream processing.

Graph Model: The computation graph is declarative: nodes are spiking neuron layers, synapse layers, delay lines, and functional kernels. The compiler flattens this into a static graph with explicit timing links.

Timing & Units: Time is first-class. Every stream has a unit (μs, ms), and all delays/latencies are specified with units. The runtime enforces these units globally. For example, a neuron with 5 ms refractory period cannot fire sooner.

Capability Negotiation: Each target publishes a Device Capability Descriptor (DCD) (resolution, dynamic range, max firing rate, jitter, clock drift). The compiler solves a constrained mapping: it partitions the graph to fit the chip’s memory/synapse budget, inserts routing tables (for multi-chip backends), and ensures worst-case timing jitter < Δ. If real-time constraints (e.g. “10 ms end-to-end latency”) can’t be met on a hardware’s clock, a warning is issued and a slower fallback is used.

Conformance Profiles: Standard profiles (e.g. BASE, REALTIME, LEARNING, LOWPOWER) define minimal op sets. A REALTIME profile might forbid software loops that exceed cycles or require precise timing; a LEARNING profile enables plasticity. This helps ensure portability – e.g. if a chip doesn’t support online STDP, we don’t use LEARNING.

Reproducibility: All stochastic processes (random weight init, dropout, Poisson inputs) use seeded RNG. The simulator enforces determinism (like NEST’s guarantees
pmc.ncbi.nlm.nih.gov
): running with the same seed on different backends yields identical high-level traces up to known ε. Checkpointing supports hot-reload and stepping, and the trace equivalence tests detect any nondeterministic drift.

(Illustrative) Architecture Diagram
   +------------+     +-----------+     +-------------+      +-------------+
   |  Sensors   |     |   SAL     |     |    EIR IR   |      |  Execution  |
   |  (DVS,     | --> |  (Drivers +| --> | (Compiler + | -->  |  Layer (NEL)|
   |   Audio,   |     |  Calibration)|   |   IR Ops)   |      |  (Backends) |
   |   IMU...)  |     +-----------+     +-------------+      +-------------+
   +------------+     | unify event|   | hardware-   |       |  Loihi/Lava |
                      | streams    |   | neutral IR  |       |  SpiNNaker  |
                      +-----------+   +-------------+       |  SynSense   |
                                          |  Emits      |       |  CPU Sim    |
                                          |  .eir files |       +-------------+
                                          +-------------+


Figure 1: EventFlow layered stack (conceptual). Events flow from sensors through the Sensor Abstraction Layer (SAL) into a unified EIR. The compiler then maps the EIR to a Neuromorphic Execution Layer (NEL) backend (chip or simulator).

Governance & Roadmap

EventFlow is envisioned as an open‑core project. Core abstractions, IR, SAL, and base modules will be Apache‑licensed. Vendor backends and advanced optimizers (e.g. proprietary quantizers) may be commercial. A public foundation will manage the specs and conformance tests, much like MLPerf for AI. Within 6–24 months we plan incremental milestones: first a working EIR+simulator, then adding real chips, benchmarks, cloud simulation, and finally community‑driven standardization. (These details follow community inputs and parallels like the NeuroBench initiative
nature.com
.)

Conclusion

By providing one API for events, EventFlow bridges the gap between neuromorphic hardware and developers. It delivers “the neuromorphic TensorFlow/PyTorch + OpenCV” – enabling event-driven vision, audio, control, and data analysis to run naturally on brains-in-silicon. Hardware vendors see a unified target, scientists see reproducible experiments, and application developers gain plug‑and‑play event intelligence.

Sources: The design draws on prior work in neuromorphic toolchains and standards. For example, Lava (Intel) maps Python networks to Loihi
open-neuromorphic.org
, and PyNN lets one code run on many SNN simulators and chips
neuralensemble.org
. Open‑Neuromorphic efforts emphasize hardware-agnostic IRs and benchmarks
open-neuromorphic.org
open-neuromorphic.org
nature.com
. EventFlow builds on these principles, adding sensor abstraction and developer tooling to make event-based computing truly accessible.
# EventFlow: Hardware- and Sensor‑Agnostic Event Computing SDK v0.1

Purpose
- Deliver a universal SDK that executes identical event‑driven application code across neuromorphic chips and event sensors with deterministic semantics and graceful fallback.
- Integrate with the existing neuro‑compiler skeleton at [../compiler/](../compiler/), reusing IR, HAL, passes, runtime, CLI, telemetry, and Python bindings.

Anchors to existing components
- IR graph type: [nir::Graph](../compiler/crates/nir/src/lib.rs:52) with attributes map for metadata
- IR serialization: [nir::Graph::to_json_string](../compiler/crates/nir/src/lib.rs:79), [nir::Graph::from_json_str](../compiler/crates/nir/src/lib.rs:82), [nir::Graph::to_yaml_string](../compiler/crates/nir/src/lib.rs:85), [nir::Graph::from_yaml_str](../compiler/crates/nir/src/lib.rs:88)
- HAL builtin targets: [hal::builtin_targets](../compiler/crates/hal/src/lib.rs:12)
- Pass framework: [passes::PassManager](../compiler/crates/passes/src/lib.rs:40), [passes::NoOpPass](../compiler/crates/passes/src/lib.rs:11), [passes::build_pipeline](../compiler/crates/passes/src/lib.rs:93)
- Runtime stubs and adaptive policy hooks: [runtime::deploy](../compiler/crates/runtime/src/lib.rs:13)
- Telemetry profile schema: [telemetry::profiling::ProfileRecord](../compiler/crates/telemetry/src/lib.rs:25)
- Python bridge stubs: [py::list_targets](../compiler/crates/py/src/lib.rs:8), [py::profile_summary_jsonl](../compiler/crates/py/src/lib.rs:29)
- CLI entrypoints: [../compiler/crates/cli/src/main.rs](../compiler/crates/cli/src/main.rs)
- Simulators to leverage: [../compiler/crates/sim_neuron/src/lib.rs](../compiler/crates/sim_neuron/src/lib.rs), [../compiler/crates/sim_coreneuron/src/lib.rs](../compiler/crates/sim_coreneuron/src/lib.rs)

---

## v0.1 Scope and determinism profile

Default v0.1 profile
- Targets: CPU simulator default, optional GPU simulator
- Vendor backends: discovered via HAL and stubbed through capability descriptors for compile‑time negotiation
- Conformance profiles: BASE and REALTIME
- Determinism tolerances:
  - Time tolerance epsilon: 100 microseconds
  - Numeric tolerance epsilon: 1e‑5 relative
  - Default mode: exact event ordering with canonical tie‑break, optional fixed step with dt 100 microseconds
- Reproducibility: seeded randomness with bit‑exact replay on the same backend and epsilon‑equivalent across backends

These are default bounds and can be tightened per app or per backend capability.

---

## Thin‑waist architecture

Mermaid

flowchart TD
A[Applications Python API] --> B[SAL Sensor Abstraction]
A --> C[Spiking Graph API]
B --> D[EIR IR with units determinism]
C --> D
D --> E[Lowering and rewrite passes]
E --> F[HAL backend registry]
F --> G[Vendor backends]
F --> H[CPU GPU simulators]
E --> I[Artifact packager EFPKG]
G --> J[Physical hardware]
H --> K[Deterministic simulator]
E --> L[Conformance suite]
K --> L
J --> L

---

## Event Intermediate Representation EIR on NIR

We adopt [nir::Graph](../compiler/crates/nir/src/lib.rs:52) as the structural backbone and carry EventFlow semantics in the `attributes` map. This preserves compatibility and avoids invasive changes for v0.1.

Required EIR attributes on nir::Graph.attributes
- eir.version: string, example 0.1.0
- eir.time_unit: string, one of ns us ms
- eir.global_clock_hz: number, effective global clock rate for scheduling
- eir.mode: string, one of exact_event fixed_step
- eir.fixed_step_dt_us: integer, only if mode fixed_step
- eir.tolerance.time_us: integer, default 100
- eir.tolerance.numeric: number, default 1e‑5
- eir.seed: integer, 64‑bit, seed for RNG across all stochastic ops
- eir.capability.requirements: object, minimal capability set expected by the application
- eir.trace.record: boolean, enable golden trace collection
- eir.trace.channels: array of strings identifying probe names or node ids
- eir.security.sandbox: boolean, enforce kernel sandboxing
- eir.security.rate_limit_keps: integer, thousands of events per second cap per channel
- eir.security.overflow_policy: string, one of drop head tail block

Using existing fields
- Populations and connections remain as in NIR; delays use [nir::Connection::delay_ms](../compiler/crates/nir/src/lib.rs:20). For microsecond precision, the compiler normalizes to eir.time_unit during lowering.

Serialization and portability
- JSON and YAML are first‑class via [nir::Graph::to_json_string](../compiler/crates/nir/src/lib.rs:79) and [nir::Graph::to_yaml_string](../compiler/crates/nir/src/lib.rs:85). Binary via feature gated bincode remains optional for compact packaging.

---

## Event Tensor abstraction

Purpose
- The Event Tensor is the fundamental sparse structure for asynchronous streams and interprocess transport.

Data model
- An Event Tensor is a stream of records with a declared dimensionality and units
  - header
    - schema_version: string
    - dims: array of named axes, e.g. [time, x, y, polarity] or [time, band, magnitude]
    - units
      - time: ns or us or ms
      - value: dimensioned unit where applicable, e.g. volt milliamp dimensionless
    - dtype: one of f32 f16 i16 u8
    - layout: coo or block
    - metadata: map
  - records
    - ts: unsigned 64, in header time unit
    - idx: array of unsigned indices of length dims minus one if time is implicit
    - val: numeric payload accommodating magnitude or current

Core operations
- window: temporal slicing by absolute or relative windows with unit checking
- coalesce: merge same idx within a window using sum max or custom kernel
- map filter reduce: functional transforms per event or per window
- fuse: multi stream alignment with jitter compensation and tolerance
- serialize transport: zero copy framing for pipes sockets shared memory

Serialization
- Default v0.1 carriage is JSON Lines for readability and conformance tooling alignment with telemetry
- Optional CBOR or MessagePack for efficiency
- Record framing aligns with telemetry so a single reader can handle traces and event streams

---

## Sensor Abstraction Layer SAL

Goals
- Uniform drivers and normalization for event sensors with timestamp synchronization, unit conversion, rate limiting, overflow protection, and spoofing detection.

Standard source types
- vision.dvs: polarity events with x y polarity and ts
- audio.mic: band or channel magnitude events with ts
- imu.6dof: axis acceleration or gyro events with ts
- tactile.array: taxel id pressure events with ts
- bio.ppg and bio.ecg: threshold or feature crossed events

Core SAL features
- clock sync: drift and jitter estimation with online correction
- calibration: device specific parameters persisted and applied
- normalization: convert vendor formats to Event Tensor header and records
- safety limits: rate caps and overflow handling per eir.security attributes
- spoofing detection: statistical anomaly checks on inter event intervals and spatial correlations

v0.1 deliverables
- DVS playback from AEDAT files to Event Tensor
- Microphone live capture to band events using streaming STFT encoder
- Shared clock reference and basic drift correction

---

## Neuromorphic Execution Layer NEL and backends

Backend discovery and manifests
- HAL provides a registry through [hal::builtin_targets](../compiler/crates/hal/src/lib.rs:12) and manifest loading
- Each backend supplies a Device Capability Descriptor DCD JSON conforming to the schema below and a mapper from EIR ops to backend primitives

Built in crates to surface as backends
- Loihi adapter: [../compiler/crates/backend_loihi/src/lib.rs](../compiler/crates/backend_loihi/src/lib.rs)
- SpiNNaker adapter: [../compiler/crates/backend_spinnaker/src/lib.rs](../compiler/crates/backend_spinnaker/src/lib.rs)
- Others as present under [../compiler/crates/](../compiler/crates/)

Simulators
- CPU neuron simulator: [../compiler/crates/sim_neuron/src/lib.rs](../compiler/crates/sim_neuron/src/lib.rs)
- CoreNeuron based simulator: [../compiler/crates/sim_coreneuron/src/lib.rs](../compiler/crates/sim_coreneuron/src/lib.rs)
- GPU simulator adapter optional under a feature flag using CUDA or a tensor framework for speed

---

## Device Capability Descriptor DCD schema

Schema skeleton JSON Schema draft

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EventFlow Device Capability Descriptor",
  "type": "object",
  "properties": {
    "name": { "type": "string" },
    "vendor": { "type": "string" },
    "family": { "type": "string" },
    "version": { "type": "string" },
    "time_resolution_ns": { "type": "integer", "minimum": 1 },
    "max_jitter_ns": { "type": "integer", "minimum": 0 },
    "deterministic_modes": { "type": "array", "items": { "enum": ["exact_event", "fixed_step"] } },
    "supported_ops": { "type": "array", "items": { "type": "string" } },
    "neuron_models": { "type": "array", "items": { "type": "string" } },
    "plasticity_rules": { "type": "array", "items": { "type": "string" } },
    "weight_precisions_bits": { "type": "array", "items": { "type": "integer" } },
    "max_neurons": { "type": "integer", "minimum": 1 },
    "max_synapses": { "type": "integer", "minimum": 1 },
    "max_fanout": { "type": "integer", "minimum": 1 },
    "memory": {
      "type": "object",
      "properties": {
        "per_core_kib": { "type": "integer" },
        "global_mib": { "type": "integer" }
      }
    },
    "routing": {
      "type": "object",
      "properties": {
        "multi_chip": { "type": "boolean" },
        "max_hops": { "type": "integer" }
      }
    },
    "power": {
      "type": "object",
      "properties": {
        "mw_per_spike_typ": { "type": "number" },
        "idle_mw": { "type": "number" }
      }
    },
    "overflow_behavior": { "enum": ["drop_head", "drop_tail", "block"] },
    "conformance_profiles": { "type": "array", "items": { "enum": ["BASE", "REALTIME", "LEARNING", "LOWPOWER"] } }
  },
  "required": ["name", "vendor", "family", "version", "time_resolution_ns", "deterministic_modes", "supported_ops"]
}
```

Compiler negotiation strategy
- Read DCD with HAL
- Normalize EIR timing to device time_resolution_ns with error tracking
- Validate constraints for selected profile
- Partition and place respecting memory and fanout
- Insert rewrites for unsupported ops or redirect to simulator partition
- Emit warnings when constraints or epsilon cannot be met
- Produce a composite plan if hybrid execution is best

---

## Deterministic time semantics

Ordering
- Primary key ts, then channel id, then spatial idx tuple, then stable ingestion order
- All operators are pure in event mode for a given seed

Modes
- exact event mode: process strictly in timestamp order and maintain canonical ordering
- fixed step mode: discretize time by dt and propagate quantization error trackers

Seeds and replay
- Use a single 64‑bit seed across all stochastic nodes
- Capture golden traces when enabled and replay to validate equivalence

Trace formats
- Event trace lines for probes
- Profile records for performance metrics using [telemetry::profiling::ProfileRecord](../compiler/crates/telemetry/src/lib.rs:25)

---

## Conformance and QA

Trace equivalence
- Compare backend outputs to golden within eir.tolerance numeric and time bounds
- Mismatch reporting includes the earliest divergence and summary statistics

Benchmark metrics
- Latency P50 P99
- Throughput events per second
- Dropped event rate
- Energy proxy from backend power model or device readouts

Security and safety
- Kernel sandbox with resource limits
- Rate limiting and overflow policies enforced by SAL and runtime
- Spoofing detection for adversarial patterns

---

## Packaging and artifact portability EFPKG

Bundle structure
- manifest.yaml: metadata with semver app id author created timestamp profiles features
- eir.json: IR with EventFlow attributes using [nir::Graph::to_json_string](../compiler/crates/nir/src/lib.rs:79)
- dcd.requirements.json: a reduced required capability set
- golden.trace.jsonl: probe events captured under seed and profile
- profile.baseline.jsonl: performance baseline optional
- signatures and hash file optional

Feature flags and semver
- SDK and model versions follow semantic versioning
- Feature flags gate optional ops or profiles with compatibility matrices

---

## Developer experience and CLI

Primary interfaces
- Python‑first high level API composing sensors modules and graphs
- Optional C++ wrapper for embedded contexts
- gRPC service mode for remote execution and cloud scaling

CLI mapping
- ef list‑targets proxies to CLI at [../compiler/crates/cli/src/main.rs](../compiler/crates/cli/src/main.rs)
- ef lower uses pass configs via [passes::PassManager](../compiler/crates/passes/src/lib.rs:40) and [passes::build_pipeline](../compiler/crates/passes/src/lib.rs:93) dumping artifacts
- ef compile resolves target through HAL and emits backend plan
- ef run orchestrates deployment through [runtime::deploy](../compiler/crates/runtime/src/lib.rs:13)
- ef profile summarizes profile JSONL using [py::profile_summary_jsonl](../compiler/crates/py/src/lib.rs:29)
- ef validate executes conformance suites comparing traces
- ef package builds EFPKG from outputs

---

## Domain modules v0.1

Vision
- Optical flow operator and corner detection optimized for DVS
- Object and gesture primitives with probe points

Audio
- Voice activity detector
- Keyword spotting for wake word

Robotics
- Reflex controller and obstacle avoidance primitive

Time series
- Anomaly detection and change‑point detection kernels

Wellness
- HRV analysis and simple stress indicator

Creative
- Event reactive generative graphics building block

Each module ships with tests demo datasets and EIR component graphs.

---

## Integration plan to existing compiler workspace

EIR envelope
- Store EventFlow metadata as keys in [nir::Graph.attributes](../compiler/crates/nir/src/lib.rs:64)
- Add deterministic and unit checks in a new pass suite

Passes
- Deterministic scheduling pass
- Time unit normalization pass
- Capability rewrite pass
- Partition and placement pass
- Trace probe insertion pass
- Use [passes::PassManager](../compiler/crates/passes/src/lib.rs:40) and extend [passes::build_pipeline](../compiler/crates/passes/src/lib.rs:93) with new pass names

Runtime
- Extend the runtime to honor global timebase seeds and scheduling hooks in [../compiler/crates/runtime/src/lib.rs](../compiler/crates/runtime/src/lib.rs)
- Add trace recorder in the telemetry format

HAL and targets
- Continue to use [hal::builtin_targets](../compiler/crates/hal/src/lib.rs:12) and target manifests under [../compiler/targets/](../compiler/targets/)
- Vendor backends load DCDs alongside target manifests

Python bindings
- Expose list targets compile simulate deploy profile summary using [../compiler/crates/py/src/lib.rs](../compiler/crates/py/src/lib.rs)
- EventFlow Python packages import those symbols and add SAL wrappers and high level graph helpers

---

## Example applications for v0.1

- Wake word detection and alert
- Optical flow fusion with gesture detection
- Time series anomaly detector for security or logs
- Drone loop demo using simulator for navigation controller
- Real time financial event predictor on synthetic event stream
- Wearable HRV stress trend monitor from prerecorded events

---

## Roadmap

Phase 1 v0.1
- Implement SAL DVS playback and audio mic
- EIR attributes and deterministic passes
- CPU simulator backend default and optional GPU simulator
- CLI wiring and EFPKG packager
- Conformance suite with golden traces and latency metrics
- Three end‑to‑end apps

Phase 2 v0.2
- First class Loihi and SpiNNaker paths with constrained profiles
- Expanded domain modules vision audio robotics
- Model hub with validation badges and compatibility matrix

Phase 3 v0.3
- Cloud execution and gRPC deployment
- Advanced quantization and autotuning passes
- Wider sensor suite and stronger spoofing detection

---

## Next actions

- Confirm v0.1 determinism epsilon bounds and profile selection
- Scaffold EventFlow packages in this workspace wired to the compiler Python bridge
- Add pass names and stubs to the passes crate and extend CLI pipelines
- Define DCD schema JSON and add validators in Python and Rust
- Implement SAL adapters and conformance harness
