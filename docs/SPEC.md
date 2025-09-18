# EventFlow SDK — Comprehensive Specification and Project Scaffold v0.1

Status
- Independent software SDK. Do not integrate or depend on external compilers; treat third-party repositories only as conceptual references.
- Deliverables: complete scaffold and documentation with stubs for all layers; deterministic execution, conformance testing, and packaging are first-class.

Related docs
- Overview: [sdk.md](sdk.md)
- Guide and scaffold summary: [docs/README.md](docs/README.md)

Table of contents
1. Goals and principles
2. Architecture overview and thin waist
3. Event Intermediate Representation (EIR)
4. Event Tensor datatype
5. Sensor Abstraction Layer (SAL)
6. Neuromorphic Execution Layer (NEL) and backends
7. Capability negotiation and Device Capability Descriptors (DCD)
8. Deterministic runtime and time semantics
9. Conformance testing and QA
10. Packaging and portability (EFPKG)
11. CLI workflows
12. Security and safety model
13. Interfaces (Python-first, optional C++ / gRPC / REST)
14. Domain modules (vision, audio, robotics, time series, wellness, creative)
15. Example applications
16. Roadmap and governance
17. Glossary

---

## 1. Goals and principles

- Hardware- and sensor-agnostic: Write once, run anywhere across neuromorphic chips and event-based sensors.
- Deterministic semantics: Exact event ordering or fixed-step modes with unit-checked temporal operations and seeded RNG; reproducible runs and cross-backend equivalence within tolerance.
- Graceful degradation: Automatic software emulation for unsupported hardware features guided by explicit capability negotiation and epsilon contracts.
- Developer productivity: Python-first API, batteries-included modules, CLI tooling, rich debugging/profiling, and shareable artifacts.
- Open specification: JSON Schemas for EIR, Event Tensor, DCD, and EFPKG to standardize interchange and validation.

---

## 2. Architecture overview and thin waist

Mermaid

flowchart TD
A[Applications Python API] --> B[SAL Sensor Abstraction]
A --> C[Spiking Graph API]
B --> D[EIR IR with units and determinism]
C --> D
D --> E[Lowering and rewrite passes]
E --> F[Backend registry]
F --> G[Vendor plugins]
F --> H[CPU GPU simulators]
E --> I[Packager EFPKG]
G --> J[Physical hardware]
H --> K[Deterministic simulator]
E --> L[Conformance suite]
K --> L
J --> L

Thin waist
- EIR acts as the hardware- and sensor-neutral representation bridging application graphs to backends.
- SAL normalizes all sensor inputs as Event Tensor streams and timestamps with synchronization.
- Backend registry provides capability-aware mapping and fallback to simulators when necessary.

---

## 3. Event Intermediate Representation (EIR)

Intent
- A typed, unit-aware intermediate representation for event-driven computation graphs supporting spiking primitives and domain kernels.
- Deterministic execution is a property of the IR configuration (time mode, tolerances, seeds) plus operator semantics.

3.1. Core entities
- Graph: name, attributes, version, profile, time, metadata.
- Node:
  - id: unique string
  - kind: one of spiking_neuron, synapse, delay_line, kernel, group, route, probe
  - params: operator-specific parameters (e.g., neuron tau, threshold)
  - state: optional initial state (membrane potentials, synaptic traces)
  - timing_constraints: deadlines, refractory periods, or max-latency budgets
- Edge:
  - src, dst: node ids
  - weight: numeric (may be quantized later)
  - delay_us: integer microseconds
  - plasticity: optional rule reference
- Probe:
  - identifiers for trace capture and QoS metrics (latency, drop rate)

3.2. Profiles
- BASE: minimal op set; deterministic modes; software fallback allowed
- REALTIME: additional timing constraints; bounded jitter; strict overflow policies
- LEARNING: online plasticity enabled (STDP/Hebbian)
- LOWPOWER: optimizations prioritize energy constraints

3.3. Time semantics in IR
- time.unit: ns | us | ms
- time.mode: exact_event | fixed_step
- time.fixed_step_dt_us: integer (required if fixed_step)
- time.epsilon_time_us: integer, tolerance for cross-backend equivalence (default 100)
- time.epsilon_numeric: number, relative tolerance (default 1e-5)
- seed: 64-bit seed for stochastic operators

3.4. JSON Schema (normative skeleton)
Note: Full schemas will live under [docs/specs/eir.schema.json](docs/specs/eir.schema.json). The skeleton below specifies required structure.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EventFlow EIR",
  "type": "object",
  "required": ["version", "profile", "time", "graph", "nodes", "edges"],
  "properties": {
    "version": { "type": "string" },
    "profile": { "enum": ["BASE", "REALTIME", "LEARNING", "LOWPOWER"] },
    "seed": { "type": "integer", "minimum": 0 },
    "time": {
      "type": "object",
      "required": ["unit", "mode"],
      "properties": {
        "unit": { "enum": ["ns", "us", "ms"] },
        "mode": { "enum": ["exact_event", "fixed_step"] },
        "fixed_step_dt_us": { "type": "integer", "minimum": 1 },
        "epsilon_time_us": { "type": "integer", "minimum": 0 },
        "epsilon_numeric": { "type": "number", "minimum": 0 }
      }
    },
    "graph": {
      "type": "object",
      "required": ["name"],
      "properties": {
        "name": { "type": "string" },
        "attributes": { "type": "object" }
      }
    },
    "nodes": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "kind"],
        "properties": {
          "id": { "type": "string" },
          "kind": { "type": "string" },
          "params": { "type": "object" },
          "state": { "type": "object" },
          "timing_constraints": { "type": "object" }
        }
      }
    },
    "edges": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["src", "dst"],
        "properties": {
          "src": { "type": "string" },
          "dst": { "type": "string" },
          "weight": { "type": "number" },
          "delay_us": { "type": "integer", "minimum": 0 },
          "plasticity": { "type": "object" }
        }
      }
    },
    "probes": {
      "type": "array",
      "items": { "type": "string" }
    },
    "metadata": { "type": "object" }
  }
}
```

3.5. Example (minimal EIR JSON)
- Two populations connected with delay and a spike-rate probe; fixed-step mode at 100 us.

```json
{
  "version": "0.1.0",
  "profile": "BASE",
  "seed": 42,
  "time": {
    "unit": "us",
    "mode": "fixed_step",
    "fixed_step_dt_us": 100,
    "epsilon_time_us": 100,
    "epsilon_numeric": 1e-5
  },
  "graph": { "name": "lif_pair" },
  "nodes": [
    { "id": "pop0", "kind": "spiking_neuron", "params": { "model": "LIF", "size": 128, "tau_ms": 10.0, "v_th": 1.0 } },
    { "id": "pop1", "kind": "spiking_neuron", "params": { "model": "LIF", "size": 128, "tau_ms": 12.5, "v_th": 1.05 } },
    { "id": "probe0", "kind": "probe", "params": { "target": "pop1", "type": "spike_rate", "window_ms": 10.0 } }
  ],
  "edges": [
    { "src": "pop0", "dst": "pop1", "weight": 0.25, "delay_us": 500, "plasticity": null }
  ],
  "probes": ["probe0"]
}
```

---

## 4. Event Tensor datatype

Intent
- Sparse, asynchronous event stream optimized for temporal windowing, fusion, and zero-copy serialization for cross-process transport.

4.1. Header
- schema_version: string (e.g., 0.1.0)
- dims: ordered axis names; time is implicit primary axis
- units: time (ns|us|ms), value (volt, amp, dimensionless, etc.)
- dtype: f32 | f16 | i16 | u8
- layout: coo | block
- metadata: free-form device/session info

4.2. Records
- ts: integer timestamp in header time unit
- idx: array of indices; length equals dims length (excluding implicit time if chosen)
- val: numeric magnitude or coded payload

4.3. Operations (unit-checked)
- window(t0, t1): temporal slice
- coalesce(window, agg): sum | max | custom
- map/filter/reduce: functional per record/window
- fuse(streams, jitter_us): align multiple streams with bounded jitter
- serialize/deserialize: JSONL primary, CBOR optional

4.4. JSON Schema (skeleton)
- Will live at [docs/specs/event_tensor.schema.json](docs/specs/event_tensor.schema.json). A short version:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EventFlow Event Tensor",
  "type": "object",
  "required": ["header", "records"],
  "properties": {
    "header": {
      "type": "object",
      "required": ["schema_version", "dims", "units", "dtype", "layout"],
      "properties": {
        "schema_version": { "type": "string" },
        "dims": { "type": "array", "items": { "type": "string" } },
        "units": {
          "type": "object",
          "properties": {
            "time": { "enum": ["ns", "us", "ms"] },
            "value": { "type": "string" }
          }
        },
        "dtype": { "enum": ["f32", "f16", "i16", "u8"] },
        "layout": { "enum": ["coo", "block"] },
        "metadata": { "type": "object" }
      }
    },
    "records": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["ts", "idx", "val"],
        "properties": {
          "ts": { "type": "integer", "minimum": 0 },
          "idx": { "type": "array", "items": { "type": "integer", "minimum": 0 } },
          "val": { "type": "number" }
        }
      }
    }
  }
}
```

4.5. Example (JSONL)
- Header line followed by events as newline-delimited JSON.

```json
{"header":{"schema_version":"0.1.0","dims":["x","y","polarity"],"units":{"time":"us","value":"dimensionless"},"dtype":"u8","layout":"coo","metadata":{"sensor":"dvs","width":346,"height":260}}}
{"ts":100,"idx":[12,45,1],"val":1}
{"ts":104,"idx":[12,45,0],"val":1}
{"ts":133,"idx":[13,45,1],"val":1}
```

---

## 5. Sensor Abstraction Layer (SAL)

Purpose
- Provide uniform drivers and normalization for event-based sensors; enforce timestamp synchronization, rate limiting, overflow protection, and spoofing detection.

5.1. Standard source types
- vision.dvs: (ts, x, y, polarity), metadata includes resolution and bias settings
- audio.mic: (ts, band, magnitude) or (ts, channel, magnitude) with encoder (e.g., streaming STFT)
- imu.6dof: (ts, axis, value) for acceleration/gyro
- tactile.array: (ts, taxel, pressure)
- bio.ppg/ecg: threshold or feature-crossing events

5.2. Clock synchronization
- Maintain per-device clock models with drift/jitter estimation
- Periodically align to a host monotonic clock using bounded-error filters
- Provide SAL-level monotonic ts ensuring consistent ordering to the runtime

5.3. Rate limiting and overflow policies
- Configurable caps (k events/s per channel) per EIR security attributes
- Overflow behaviors: drop_head | drop_tail | block (real-time profile may forbid blocking)
- Backpressure signals to upstream acquisition when possible

5.4. Spoofing detection (baseline)
- Detect anomalous inter-event interval distributions
- Spatial correlation checks (e.g., excessive simultaneous pixel flips)
- Heuristics configurable per sensor type; log anomalies to telemetry

5.5. v0.1 drivers (stubs)
- DVS playback: AEDAT reader to Event Tensor JSONL stream
- Microphone: system audio capture to band events via streaming STFT

---

## 6. Neuromorphic Execution Layer (NEL) and backends

Definition
- Logical layer that executes EIR graphs on available targets or simulators, abstracted behind a backend plugin interface.
- v0.1: software-only backends (CPU-sim default, GPU-sim optional).

Backend plugin interface (conceptual)
- name(), version(), supported_ops(), deterministic_modes()
- load_dcd(descriptor: json) -> capability object
- compile(eir) -> plan (with partitions, schedules, warnings)
- run(plan, streams) -> traces, profiles

Registration and discovery
- Backends register via entry points (Python package metadata) or module registry.
- DCD provided as JSON files shipped with backend packages.

---

## 7. Capability negotiation and Device Capability Descriptors (DCD)

Purpose
- Mediate between requested EIR features and backend capabilities, generating a feasible plan or a composite plan with fallbacks.

7.1. DCD JSON Schema (skeleton)
- Full schema will live at [docs/specs/dcd.schema.json](docs/specs/dcd.schema.json).

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EventFlow DCD",
  "type": "object",
  "required": ["name", "vendor", "family", "version", "time_resolution_ns", "deterministic_modes", "supported_ops"],
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
    "memory": { "type": "object" },
    "routing": { "type": "object" },
    "power": { "type": "object" },
    "overflow_behavior": { "enum": ["drop_head", "drop_tail", "block"] },
    "conformance_profiles": { "type": "array", "items": { "enum": ["BASE", "REALTIME", "LEARNING", "LOWPOWER"] } }
  }
}
```

7.2. Negotiation algorithm (high-level)
- Validate EIR profile against DCD conformance_profiles; if mismatch, suggest alternate profile or fallback.
- Normalize timing to device time_resolution_ns; compute quantization error; ensure epsilon_time_us bounds.
- Check opset coverage; for unsupported ops, select software emulation or degrade with explicit contracts.
- Partition graph by memory and fanout constraints; generate schedules with bounded jitter.
- Emit plan with warnings for any constraints unmet; propose fixed_step if exact_event cannot be realized.

---

## 8. Deterministic runtime and time semantics

Modes
- exact_event: Strict timestamp order; stable tie-breaker: channel, spatial idx tuple, ingestion order.
- fixed_step: Discrete dt; accumulate quantization error; ensure monotonic step progression.

Seeded reproducibility
- Single 64-bit global seed; all stochastic sources derive per-operator streams via counter-based RNG to avoid order-dependent artifacts.

Trace and replay
- Golden traces captured from probes; replay runner enforces equivalence within epsilon bounds on time/numeric differences.

Overflow and rate handling
- Runtime enforces SAL-provided caps and EIR overflow policies; REALTIME profile forbids unbounded buffering.

---

## 9. Conformance testing and QA

Trace equivalence suite
- Input datasets (DVS recordings, audio clips, IMU sequences)
- Execute across backends; compare output probes against golden traces
- Report earliest divergence, summary stats, and pass/fail per epsilon bounds

Performance benchmarks
- Latency P50/P99, throughput events/s, dropped event rate
- Energy proxy where device power models exist; simulators report estimated metrics

Profiles and badges
- Profile-specific test sets (BASE, REALTIME, LEARNING)
- Conformance badges recorded in compatibility matrices (eventflow-hub)

---

## 10. Packaging and portability (EFPKG)

Bundle structure
- manifest.yaml: sdk_version, model_id, profile, created, author, features
- eir.json: EIR graph and configuration
- dcd.requirements.json: minimal capability set required (subset of DCD schema)
- golden.trace.jsonl: probe events under a specified seed/profile
- profile.baseline.jsonl: optional performance baseline
- signatures.txt and sha256sums.txt: optional integrity metadata

Semver and feature flags
- Models and SDK use semantic versioning; feature flags declare optional ops or kernels and compatibility matrices.

---

## 11. CLI workflows

Commands (conceptual)
- ef build: validate EIR, generate plan (simulator by default)
- ef run: execute plan on selected backend or simulator
- ef profile: summarize JSONL telemetry (latency, throughput, drops)
- ef validate: run conformance suite against golden traces
- ef package: assemble EFPKG bundle
- ef list-backends: list discovered backends and capability summaries

Outputs
- Structured run directories with plan.json, logs, profile.jsonl, traces, artifacts

---

## 12. Security and safety model

Sandboxing
- User kernels run in restricted environments; no arbitrary system calls
- Resource limits on CPU, memory, file I/O, and network (off by default for local dev)

Rate limiting and overflow
- Enforced at SAL and runtime per EIR policies; logs and counters for all drops

Spoofing detection
- Heuristic detectors per sensor type with pluggable rules and thresholds

Artifact provenance
- Bundle signatures and checksums; optional SBOM for dependencies

---

## 13. Interfaces

13.1. Python-first API (illustrative)
- sensors.open("vision.dvs://..."), sensors.open("audio.mic://...")
- vision.optical_flow(), vision.corner_detect(), audio.keyword_spotter()
- fusion.coincidence(streams, window="50 ms")
- compile_and_run(graph, backend="auto", constraints={"latency":"10ms"})

13.2. C++ embedding (optional)
- Minimal header-only façade mirroring Python semantics for deployment on constrained environments.

13.3. gRPC service (optional)
- Service for remote execution, packaging, profiling, and conformance runs; protobufs under interfaces/rpc/.

13.4. REST gateway (optional)
- OpenAPI spec for simple operations (run, profile, validate, package).

---

## 14. Domain modules

Vision
- Optical flow, corner detection, object tracking, gestures
- Event-native operators; probe points for traces

Audio
- VAD, keyword spotting, speaker diarization (stub), spatial localization (stub)

Robotics
- Reflex controllers, event-based SLAM primitives (stub), obstacle avoidance

Time series
- Anomaly detection, change-point detection, adaptive forecasting

Wellness
- HRV analysis, sleep event segmentation, stress indicators

Creative
- Bio-adaptive music sequencing, event-reactive generative graphics

Each module ships with EIR component graphs, unit tests, and example datasets pointers.

---

## 15. Example applications

- Wake-word detection system using audio.mic and keyword_spotter
- Optical flow + gesture fusion demo for event camera
- Time series anomaly-based security monitor
- Drone navigation controller (simulated sensors + reflex)
- Real-time financial prediction on synthetic events
- Wearable HRV stress monitoring from prerecorded events

Each example provides: build/run scripts, EIR graphs, golden traces, and EFPKG bundles.

---

## 16. Roadmap and governance

Phases
- v0.1: Independent SDK core, EIR/Event Tensor/DCD/EFPKG schemas, SAL (DVS+mic), CPU-sim, CLI, conformance suite, docs, and three end-to-end examples.
- v0.2: GPU-sim, expanded domain modules, initial vendor plugin adapters out-of-tree.
- v0.3: Cloud-native deployment, gRPC/REST services, advanced quantization/auto-tuning.

Governance
- Permissive license for core; contribution guidelines; conformance badges in eventflow-hub.

---

## 17. Glossary

- EIR: Event Intermediate Representation
- SAL: Sensor Abstraction Layer
- NEL: Neuromorphic Execution Layer
- DCD: Device Capability Descriptor
- EFPKG: EventFlow Package bundle
- Exact-event mode: strictly ordered event processing
- Fixed-step mode: discretized temporal execution with dt and error tracking