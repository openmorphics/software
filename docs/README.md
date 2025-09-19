# EventFlow: A Universal, Deterministic Event-Driven Computing SDK

[![Build](https://img.shields.io/badge/build-GitHub%20Actions-blue?logo=github)](https://github.com/your-org/eventflow/actions)
[![License](https://img.shields.io/badge/License-BSD--3--Clause-green.svg)](../LICENSE)

EventFlow is a modular, Python-first framework for neuromorphic and event-driven data processing that runs identically across heterogeneous hardware backends and sensor modalities. It provides:

- A thin-waist Event Intermediate Representation (EIR) for portable, deterministic execution.
- A Sensor Abstraction Layer (SAL) that unifies event sensors including DVS cameras, event microphones, tactile arrays, and IMUs.
- A Spiking Graph API with neuromorphic primitives (spiking neurons, plastic synapses, delays, and hypergraphs).
- Cross-backend compilation and deterministic replay of execution traces with conformance validation.
- Software fallback and graceful degradation when hardware features are unavailable.

This document is the top-level guide to the EventFlow ecosystem: architecture, packages, installation, quick start, API docs, development, testing, contributions, roadmap, and troubleshooting.

---

## Contents

- Overview
- Architecture
- Packages
- Installation
- Quick Start
- API Documentation
- Development Guide
- Testing
- Contributing
- Roadmap
- Troubleshooting
- License

---

## Overview

EventFlow enables writing event-driven applications once and running them anywhere:

- Across any neuromorphic chip (e.g., Intel Loihi, SpiNNaker, SynSense, custom ASIC).
- Across software backends (high-accuracy CPU and GPU simulators).
- Across event-based sensors (DVS, audio, tactile, IMU), with unified bindings.
- With deterministic time semantics, unit-checked temporal operations, and bit-exact replay under standardized tolerances.

Core properties:

- Determinism: Canonical event ordering, seeded randomness policy, consistent unit systems, and trace equivalence tooling.
- Portability: Target-independent EIR, capability negotiation, and automatic emulation fallback where necessary.
- Productivity: Batteries-included modules for vision/audio/robotics/timeseries/wellness/creative domains.
- Operability: Conformance tests, profiling, packaging, model hub, and CLI.

---

## Architecture

High-level layers:

1) Applications
   - Compose spiking graphs using domain modules; bind to sensors via SAL.
2) EventFlow Core (Thin Waist)
   - EIR (Event Intermediate Representation)
   - Compiler/Planner (capability negotiation, schedule planning)
   - Runtime (event-driven and fixed-Δt executors)
   - Conformance (trace capture, comparison, metrics)
3) Backends
   - Vendor plugins (Loihi/Lava, SpiNNaker, SynSense, BrainScaleS)
   - CPU/GPU simulators (timing-accurate, deterministic)
4) SAL (Sensor Abstraction Layer)
   - Uniform packet format, replay/stream APIs, clock sync, rate limiting, spoof detection
5) Hub (Model/Artifact Registry)
   - Packaging, capability manifests, golden traces, compatibility matrices

Key abstractions:

- Event Tensor: Sparse event streams over arbitrary dimensions with temporal windowing and efficient serialization.
- Spiking Graph: Declarative pipelines with neurons/synapses/delays and hypergraph connectivity.
- Device Capability Descriptors (DCD): JSON/Schema described device capabilities for negotiation and planning.
- EIR Packages (EFPKG): Self-contained deployables (EIR bytecode, capabilities, golden traces, version metadata).

---

## Packages

The EventFlow ecosystem is split into modular Python distributions:

- eventflow-core
  - EIR types/serialization
  - Compiler/planner and runtime executors
  - Conformance testing (trace/metrics)
  - Documentation: See the package README

- eventflow-sal (Sensor Abstraction Layer)
  - Canonical event packet formats
  - Source registry (DVS/audio/IMU/tactile)
  - Clock sync, telemetry, rate limiting, spoof detection
  - Documentation: See the package README

- eventflow-modules
  - Domain modules for vision, audio, robotics, time series, wellness, and creative
  - Provide reusable EIR graph fragments and operators
  - Documentation: See the package README

- eventflow-backends
  - Backend plugin API and registry
  - CPU simulator backend (runnable reference)
  - Vendor backends as structured stubs
  - Documentation: See the package README

- eventflow-cli
  - Command-line interface for build, run, profile, validate
  - Integrates core/backends/hub workflows
  - Documentation: See the package README

- eventflow-hub
  - Local model/artifact registry
  - Packing/unpacking of deployable bundles
  - Future: remote hub client
  - Documentation: See the package README

Direct links to package docs:
- eventflow-core: ../eventflow-core/README.md
- eventflow-sal: ../eventflow-sal/README.md
- eventflow-modules: ../eventflow-modules/README.md
- eventflow-backends: ../eventflow-backends/README.md
- eventflow-cli: ../eventflow-cli/README.md
- eventflow-hub: ../eventflow-hub/README.md

---

## Installation

Requirements:
- Python 3.11+
- macOS/Linux (Windows via WSL recommended)
- Optional: CUDA-capable GPU for gpu-sim backends (future)
- Optional: Vendor SDKs (e.g., Lava/Loihi) for specific hardware backends

Recommended: Create a virtual environment:

```
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install individual packages (editable dev mode):

```
pip install -e ./eventflow-core
pip install -e ./eventflow-sal
pip install -e ./eventflow-modules
pip install -e ./eventflow-backends
pip install -e ./eventflow-cli
pip install -e ./eventflow-hub
```

Full ecosystem (monorepo dev):

```
pip install -e ./eventflow-core ./eventflow-sal ./eventflow-modules ./eventflow-backends ./eventflow-cli ./eventflow-hub
```

---

## Quick Start

1) Build a minimal bundle
- Create a trivial EIR file (JSON or serialized form). For early smoke tests you can use an empty JSON as a placeholder while wiring real graphs.

```
mkdir -p build
eventflow build --model path/to/model.eir --out build/
```

Outputs:
- build/model.eir
- build/cap.json
- build/card.json
- build/trace.json

2) Run on CPU simulator

```
eventflow run --bundle build/ --backend cpu_sim
```

The CPU simulator provides deterministic synthetic inputs (until you supply real inputs via SAL or programmatically through eventflow-core).

3) Profile latency

```
eventflow profile --bundle build/ --backend cpu_sim
```

Reports approximate runtime metrics (latency; energy placeholder).

4) Validate against a golden trace

```
eventflow validate --bundle build/ --golden path/to/golden_trace.json
```

Checks trace equivalence with specified tolerances (wired in eventflow-core conformance tools).

5) Stream from a sensor (SAL)
- See eventflow-sal README for streaming and replay examples. The SAL normalizes real sensor events to EventFlow packets, enabling identical pipeline behavior across simulated and physical sources.

---

## API Documentation

High-level structure:

- eventflow-core
  - eir.types, eir.ops, eir.graph, eir.serialize
  - runtime.exec (event-driven and fixed-Δt)
  - conformance.compare (trace equivalence)
  - validators (EIR/Event Tensor/DCD/EFPKG)

- eventflow-sal
  - api.packet (EventPacket constructors for DVS/audio/IMU/tactile)
  - api.source (BaseSource/Replayable)
  - api.dcd (DeviceCapabilityDescriptor, validation)
  - api.uri (parse_sensor_uri)
  - registry (driver resolution)
  - sync (clock, watermark)
  - calib (calibration hooks)
  - drivers (DVS, WAV/audio, IMU/CSV, tactile)

- eventflow-modules
  - vision (optical flow, corners, gestures, tracking)
  - audio (VAD, KWS, diarization, localization)
  - robotics (reflex, SLAM, obstacle avoidance, motor control)
  - timeseries (anomaly, pattern mining, change-point, forecasting)
  - wellness (HRV, sleep, stress)
  - creative (bio-adaptive music, generative graphics)

- eventflow-backends
  - api (Backend interface, DCD)
  - registry and vendor backends
  - cpu_sim backend uses eventflow-core runtime

- eventflow-hub
  - schemas (ModelCard, CapManifest, TraceMeta)
  - pack/unpack (tar.gz bundles)
  - registry (local filesystem index)
  - client (local and future remote hub)

Each package’s README contains deeper details and examples.

---

## Development Guide

- Python 3.11+ required
- Style: PEP8, type hints encouraged
- License: BSD-3-Clause
- Virtual environment recommended (see Installation)

Repository layout (monorepo):

```
eventflow-core/
eventflow-sal/
eventflow-modules/
eventflow-backends/
eventflow-cli/
eventflow-hub/
docs/
```

Editable installation for local development:

```
pip install -e ./eventflow-core ./eventflow-sal ./eventflow-modules ./eventflow-backends ./eventflow-cli ./eventflow-hub
```

Run unit tests (per package):

```
python -m unittest discover -s eventflow-core/tests
python -m unittest discover -s eventflow-sal/tests
python -m unittest discover -s eventflow-backends/tests
python -m unittest discover -s eventflow-cli/tests
python -m unittest discover -s eventflow-hub/tests
python -m unittest discover -s eventflow-modules/tests  # as tests are added
```

---

## Testing

Testing layers:

- Unit tests
  - Validators (EIR/Event Tensor/DCD/EFPKG)
  - SAL packet/URI parsing, replay determinism
  - Backend registry and CPU simulator
  - CLI smoke tests

- Integration tests (as implemented)
  - SAL→core runtime graphs
  - Multi-backend conformance with golden traces
  - Packaging and registry round-trips

- Conformance harness (planned)
  - Automated cross-backend runs, metrics aggregation, report/badge generation

Run all tests (example):

```
pytest  # if using pytest
# or:
python -m unittest discover
```

---

## Contributing

We welcome contributions! Please:

- File issues describing bugs/feature requests.
- Open PRs with:
  - Tests covering new functionality
  - Documentation updates (README, docs/)
  - Adherence to determinism and portability constraints
- Code style: PEP8; include type hints and docstrings.
- CI: Ensure unit tests pass; add coverage for new code paths.
- Security: Avoid unsafe eval/imports; validate inputs; keep sandboxes in mind for untrusted kernels.

Roadmap items are tagged in issues; feel free to pick “good first issue” labels.

---

## Roadmap (Highlights)

- Backend capability negotiation (expanded)
  - Profile gating, time quantization checks, overflow policies, emulated ops reporting
- Deterministic schedulers
  - Exact-event and fixed-Δt with delay lines, LIF, plasticity primitives
- Full conformance harness CLI
  - Multi-backend orchestration, latency/power/drops metrics, badges
- SAL enhancements
  - Clock drift/jitter modeling, telemetry, spoofing detection, rate limiting
- EFPKG finalization
  - Hashes, sizes, validate-all workflow
- Domain modules
  - End-to-end examples across vision/audio/robotics/timeseries/wellness/creative
- Security sandboxing
  - Resource limits; kernel isolation; policy surfaces via CLI
- Cloud/distribution integrations
  - gRPC/REST services, ONNX interop, container orchestration

---

## Troubleshooting

- ImportErrors with CLI or backends:
  - Ensure packages are installed in the same environment: `pip install -e ./eventflow-...`
  - Verify `python -c "import eventflow_core; import eventflow_backends"` works.

- CLI “run/profile/validate” fails on model load:
  - Confirm `build/model.eir` exists and is valid.
  - Ensure eventflow-core is installed; backends lazily import core on demand.

- SAL replay produces no events:
  - Check the file format and driver selection (e.g., `.aedat4` for DVS, `.wav` for audio, `.csv` for IMU).
  - Use SAL telemetry/debug mode as documented in eventflow-sal/README.

- Non-deterministic traces:
  - Check epsilon configuration in conformance tools.
  - Ensure fixed seeds for any stochastic components.
  - Confirm backend time resolution meets epsilon_time_ns constraints.

- Backend unsupported features:
  - Planner will emulate unsupported operations in software with a warning.
  - Review the Device Capability Descriptor (DCD) and adjust profiles or constraints.

---

## License

BSD-3-Clause. See ../LICENSE.
