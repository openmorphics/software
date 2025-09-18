# EventFlow SDK — Comprehensive Scaffold and Specifications v0.1

Status
- Independent SDK. Do not integrate or depend on [../compiler](../compiler). Use it only as a conceptual reference.
- Primary deliverable: complete scaffold and documentation with stubs for all layers. Deterministic execution and conformance are first-class.

Canonical documents
- Overview and plan: [sdk.md](sdk.md)
- This specification: [docs/README.md](docs/README.md)
- Schemas to be authored later (referenced now for structure):
  - EIR JSON Schema: [docs/specs/eir.schema.json](docs/specs/eir.schema.json)
  - Event Tensor JSON Schema: [docs/specs/event_tensor.schema.json](docs/specs/event_tensor.schema.json)
  - Device Capability Descriptor JSON Schema: [docs/specs/dcd.schema.json](docs/specs/dcd.schema.json)
  - EFPKG Manifest Schema: [docs/specs/efpkg.schema.json](docs/specs/efpkg.schema.json)

Repository scaffold (proposed)

```
eventflow/
├── eventflow-core/               # Python package: EIR, Event Tensor, graph API, runtime, fallback, conformance
│   ├── eir/                      # EIR types and validation (pure Python + JSON Schema)
│   ├── graph/                    # Spiking Graph API and ops
│   ├── runtime/                  # Deterministic scheduler, seeds, trace recorder
│   ├── event_tensor/             # Sparse tensor type, windowing, serialization
│   ├── fallback/                 # Software emulation of unsupported features
│   ├── conformance/              # Trace equivalence, benchmark harness
│   └── __init__.py
├── eventflow-sal/                # Python package: Sensor Abstraction Layer
│   ├── drivers/                  # dvs/, audio/, imu/, tactile/, bio/
│   ├── formats/                  # AEDAT reader, JSONL streams
│   ├── sync/                     # clock sync, rate limiting, spoofing detection
│   └── __init__.py
├── eventflow-backends/           # Python package: backend registry and plugins
│   ├── registry/                 # discovery, capability negotiation
│   ├── cpu_sim/                  # reference simulator (deterministic)
│   ├── gpu_sim/                  # optional accelerated simulator (feature-flag)
│   ├── vendor/                   # plugin interface and stubs (no vendor code required)
│   └── __init__.py
├── eventflow-cli/                # Python package: ef CLI
│   └── ef.py
├── eventflow-modules/            # Domain libraries (Python)
│   ├── vision/
│   ├── audio/
│   ├── robotics/
│   ├── timeseries/
│   ├── wellness/
│   └── creative/
├── eventflow-hub/                # Local registry client, packaging, compatibility matrices
├── interfaces/
│   ├── cxx/                      # C++ headers for embedding (optional)
│   ├── rpc/                      # gRPC protobufs and service stubs (optional)
│   └── rest/                     # OpenAPI spec (optional)
├── docs/                         # Specifications and guides (this file)
├── examples/                     # End-to-end sample apps and datasets pointers
├── tests/                        # Unit, integration, conformance
└── tools/                        # Dev utilities
```

Architecture thin waist

Mermaid

flowchart TD
A[Apps Python API] --> B[SAL]
A --> C[Spiking Graph API]
B --> D[EIR units determinism]
C --> D
D --> E[Passes and rewrites]
E --> F[Backend registry]
F --> G[Vendor plugins]
F --> H[CPU GPU simulators]
E --> I[Packager EFPKG]
G --> J[Hardware]
H --> K[Deterministic simulator]
E --> L[Conformance]
K --> L
J --> L

Event Intermediate Representation EIR (overview)

Goals
- Hardware-agnostic, sensor-agnostic representation of event-driven graphs
- Unit-checked temporal semantics with deterministic execution modes
- Extensible opset covering neuron models, synapses, delays, plasticity, domain kernels

Core graph entities
- graph: name, metadata, attributes
- node: type, parameters, state, timing_constraints
- edge: connectivity, delay, weight, plasticity
- probe: named measurement channels

Determinism and time
- modes: exact_event and fixed_step
- time_unit: ns us ms
- tolerances: epsilon_time_us, epsilon_numeric
- canonical_order: tie-break by channel, spatial idx, ingestion order

JSON Schema skeleton (to be split into [docs/specs/eir.schema.json](docs/specs/eir.schema.json))

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EventFlow EIR",
  "type": "object",
  "required": ["version", "graph", "nodes", "edges", "time"],
  "properties": {
    "version": { "type": "string" },
    "profile": { "enum": ["BASE", "REALTIME", "LEARNING", "LOWPOWER"] },
    "time": {
      "type": "object",
      "properties": {
        "unit": { "enum": ["ns", "us", "ms"] },
        "mode": { "enum": ["exact_event", "fixed_step"] },
        "fixed_step_dt_us": { "type": "integer", "minimum": 1 },
        "epsilon_time_us": { "type": "integer", "minimum": 0 },
        "epsilon_numeric": { "type": "number", "minimum": 0 }
      },
      "required": ["unit", "mode"]
    },
    "graph": {
      "type": "object",
      "properties": {
        "name": { "type": "string" },
        "attributes": { "type": "object" }
      },
      "required": ["name"]
    },
    "nodes": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "kind": { "type": "string" },
          "params": { "type": "object" },
          "state": { "type": "object" },
          "timing_constraints": { "type": "object" }
        },
        "required": ["id", "kind"]
      }
    },
    "edges": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "src": { "type": "string" },
          "dst": { "type": "string" },
          "weight": { "type": "number" },
          "delay_us": { "type": "integer", "minimum": 0 },
          "plasticity": { "type": "object" }
        },
        "required": ["src", "dst"]
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

Event Tensor (overview)

Purpose
- Sparse, asynchronous event stream datatype with units and dimensionality
- Optimized for windowing, fusion, and serialization

Schema skeleton (to be split into [docs/specs/event_tensor.schema.json](docs/specs/event_tensor.schema.json))

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EventFlow Event Tensor",
  "type": "object",
  "required": ["header", "records"],
  "properties": {
    "header": {
      "type": "object",
      "properties": {
        "schema_version": { "type": "string" },
        "dims": { "type": "array", "items": { "type": "string" } },
        "units": {
          "type": "object",
          "properties": { "time": { "enum": ["ns", "us", "ms"] }, "value": { "type": "string" } }
        },
        "dtype": { "enum": ["f32", "f16", "i16", "u8"] },
        "layout": { "enum": ["coo", "block"] },
        "metadata": { "type": "object" }
      },
      "required": ["schema_version", "dims", "units", "dtype", "layout"]
    },
    "records": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "ts": { "type": "integer", "minimum": 0 },
          "idx": { "type": "array", "items": { "type": "integer", "minimum": 0 } },
          "val": { "type": "number" }
        },
        "required": ["ts", "idx", "val"]
      }
    }
  }
}
```

Device Capability Descriptor DCD (overview)

Purpose
- Declare backend capabilities, constraints, deterministic modes, timing granularity, memory budgets, and power model hooks

Schema skeleton (to be split into [docs/specs/dcd.schema.json](docs/specs/dcd.schema.json))

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

Deterministic runtime scheduler (overview)

Modes
- exact_event: strict timestamp order; tie-break on channel, idx, ingestion
- fixed_step: discretize by dt; track quantization error and ensure bounded drift

Replay
- Global 64-bit seed; capture and replay golden traces; epsilon-based equivalence checker

Sensor Abstraction Layer SAL (overview)
- Normalize vendor streams to Event Tensor
- Clock sync and drift correction
- Rate limiting, overflow policies, spoofing detection
- v0.1 drivers: DVS playback (AEDAT), microphone encoder (band events)

Backend architecture (overview)
- Backend registry and auto-selection by DCD
- CPU-sim as reference default; GPU-sim optional
- Vendor plugin interface without any vendor code in-tree

Conformance and QA (overview)
- Trace Equivalence Suite: compare outputs to golden trace with epsilon bounds
- Benchmarks: latency P50 P99, throughput, dropped rate, power proxy

Packaging EFPKG (overview)
- manifest.yaml, eir.json, dcd.requirements.json, golden.trace.jsonl, profile.baseline.jsonl
- Semantic versioning and feature flags with compatibility matrices

CLI (overview)
- ef build, ef run, ef profile, ef validate, ef package
- Consistent outputs and JSONL telemetry

Domain modules and examples (overview)
- Vision: optical flow, corners, object tracking, gestures
- Audio: VAD, KWS, spatial localization
- Robotics: reflex, SLAM primitives, obstacle avoidance
- Time series: anomaly detection, change-point, adaptive forecasting
- Wellness: HRV, sleep segmentation, stress detection
- Creative: bio-adaptive sequencing, generative graphics
- Examples: wake word, optical flow + gesture fusion, anomaly detection, drone loop, finance predictor, wearable HRV

Governance and roadmap
- License: permissive for core SDK; enterprise plugins may be commercial
- Conformance badges and open model hub
- Roadmap phases v0.1 core SDK, v0.2 vendor adapters, v0.3 cloud deployment

Next steps
- Accept this scaffold and generate initial directories and stub files
- Author schemas under docs/specs and wire ef CLI doc strings to behaviors
- Populate examples and conformance datasets