# EventFlow: Universal SDK for Neuromorphic and Event‑Based Computing

EventFlow is a universal, deterministic SDK for building event‑driven applications that run unchanged across neuromorphic chips and conventional hardware. It provides:

- A Python‑first API (optional C++ and gRPC planned) and a consistent CLI
- A unified Event Tensor data model for sparse asynchronous streams
- An Event Intermediate Representation (EIR) capturing computational graphs, neuromorphic timing constraints, and determinism contracts
- A Sensor Abstraction Layer (SAL) for multi‑modal event sources (DVS vision, audio, tactile/IMU)
- Automatic backend selection with device capability negotiation and graceful software emulation fallbacks
- Deterministic CPU/GPU simulators and vendor backends (Loihi, SpiNNaker, SynSense, ASICs) via plugins
- Conformance, debugging, and profiling tools that work identically in simulation and on hardware

Deterministic replay and conformance testing ensure bit‑exact or epsilon‑bounded equivalence across backends, enabling reproducible research and robust production deployment.


## Architecture Overview

EventFlow is organized in layers:

- eventflow-core — runtime engine, EIR compiler, deterministic operators, Event Tensor, trace IO
- eventflow-sal — Sensor Abstraction Layer (SAL) with hardware‑agnostic bindings and timestamp synchronization
- eventflow-backends — execution engines (cpu-sim, gpu-sim, vendor plugins) with capability negotiation
- eventflow-cli — `ef` command‑line tool for validate → build → run → compare → package workflows
- eventflow-modules — domain libraries (vision, audio, robotics, time series, wellness, creative)
- tools, docs, examples, tests — generators, documentation, ready‑to‑run apps, and conformance suites

High‑level dataflow:

```
Sensors (DVS / Mic / IMU / ...) --SAL--> Event Tensor JSONL
                                  |
                                  v
                       EIR Graph (operators + timing/units)
                                  |
                 Planner + Capability Negotiation (DCD)
                                  |
                   Backend (CPU/GPU/Vendor) Executor
                                  |
                                  v
                          Traces / Probes / Metrics
```

Core design principles:
- Identical application code across modalities and hardware
- Deterministic execution semantics and reproducible traces
- Graceful degradation via emulation with declared tolerance bounds
- Batteries‑included module library and examples


## Key Concepts

- Event Tensor: Sparse, asynchronous, unit‑checked event streams with arbitrary dimensional indices, temporal windowing, and efficient serialization.
- Spiking Graph API: Declarative composition of event‑driven pipelines with first‑class spiking primitives (neurons, plastic synapses, delays, hypergraph connectivity).
- Event Time Semantics: Unit‑checked temporal operations, consistent voltage/current representations, deterministic replay, and trace conformance.
- EIR (Event Intermediate Representation): Target‑independent graph IR capturing both compute and timing constraints.
- Capability Negotiation (DCD): JSON‑schema device descriptors define supported features, time resolution, overflow policies, and profiles; planners adapt graphs accordingly.


## Installation

Prerequisites
- Python 3.9+ (3.9/3.10 recommended)
- macOS, Linux (Windows via WSL)
- Optional: `numpy` for accelerated SAL transforms; GPU backend requires CUDA/driver stack

Clone and install editable packages (recommended for development):

```bash
git clone <this-repo> eventflow
cd eventflow

# Core runtime and EIR
pip install -e ./eventflow-core

# Sensor Abstraction Layer
pip install -e ./eventflow-sal

# Backends (cpu-sim, gpu-sim; vendor plugins optional)
pip install -e ./eventflow-backends

# CLI tool
pip install -e ./eventflow-cli

# Domain modules (vision, audio, robotics, etc.)
pip install -e ./eventflow-modules
```

Verify installation:

```bash
ef --help
```

Optional extras:

```bash
# Speed up some SAL paths (optional)
pip install numpy

# Development / testing
pip install pytest jsonschema rich
```


## Getting Started (5 minutes)

1) Generate a deterministic audio WAV and run a simple wake‑word pipeline:

```bash
# Create a 1 kHz, 1 s mono WAV (16 kHz sampling)
python tools/gen_sine_wav.py --path examples/wakeword/audio.wav

# Normalize audio to Event Tensor bands via SAL
ef --json sal-stream \
  --uri "audio.mic://file?path=examples/wakeword/audio.wav&window_ms=20&hop_ms=10&bands=32" \
  --out out/audio_bands.jsonl --telemetry-out out/audio_bands.telemetry.json

# Execute the EIR graph on deterministic cpu-sim backend
ef run --eir examples/wakeword/eir.json --backend cpu-sim \
  --input out/audio_bands.jsonl --trace-out out/wakeword.trace.jsonl

# (Optional) Compare against golden reference
ef --json compare-traces --golden examples/wakeword/traces/golden/wakeword.golden.jsonl \
  --candidate out/wakeword.trace.jsonl --eps-time-us 50 --eps-numeric 1e-5
```

2) Run vision corner tracking with a tiny synthetic DVS stream:

```bash
# Generate a small DVS JSONL
python tools/gen_dvs_synthetic.py --path examples/vision_corner_tracking/traces/inputs/corner_sample.jsonl

# (Optional) Normalize via SAL to enforce headers, ordering, telemetry
ef --json sal-stream \
  --uri "vision.dvs://file?format=jsonl&path=examples/vision_corner_tracking/traces/inputs/corner_sample.jsonl" \
  --out out/corner.norm.jsonl --telemetry-out out/corner.telemetry.json

# Execute
ef run --eir examples/vision_corner_tracking/eir.json --backend cpu-sim \
  --input out/corner.norm.jsonl --trace-out out/corner.trace.jsonl
```

3) Run IMU‑driven robotics SLAM primitive:

```bash
# Normalize IMU CSV to Event Tensor JSONL via SAL
ef --json sal-stream \
  --uri "imu.6dof://file?path=examples/robotics_slam/traces/inputs/imu_sample.csv" \
  --out out/imu.norm.jsonl --telemetry-out out/imu.telemetry.json

# Execute SLAM EIR
ef run --eir examples/robotics_slam/eir.json --backend cpu-sim \
  --input out/imu.norm.jsonl --trace-out out/robotics_slam.trace.jsonl
```


## Multi‑Modal Data Support (SAL)

EventFlow’s SAL provides hardware‑agnostic sensor bindings with deterministic normalization (canonical sort by timestamp then index, unit headers, telemetry counters, overflow/spoof heuristics).

Supported URI schemes:
- Vision (DVS)
  - `vision.dvs://file?format=jsonl&path=<path>` — Read DVS JSONL files
  - Future: `vision.dvs://device?...` — Live camera streams
- Audio (Microphone/WAV)
  - `audio.mic://file?path=<wav>&window_ms=<int>&hop_ms=<int>&bands=<int>` — Deterministic STFT→Mel bands
- IMU (6‑DoF)
  - `imu.6dof://file?path=<csv>` — Normalize CSV (accel/gyro) to Event Tensor

Outputs:
- Event Tensor JSONL with header record (schema version, dims, dtype, units, layout) followed by event records:
  - Header: `{"header": {...}}`
  - Event record: `{"ts": <int>, "idx": [...], "val": <number|int>}`
- Telemetry JSON with counts, rates, and sync metadata: `--telemetry-out <file>`

Generators:
- Audio WAV: [tools/gen_sine_wav.py](tools/gen_sine_wav.py)
- Synthetic DVS: [tools/gen_dvs_synthetic.py](tools/gen_dvs_synthetic.py)


## Event Intermediate Representation (EIR)

EIR is a target‑independent IR that captures:
- Nodes (operators) and edges (signal flow) with neuromorphic primitives (spiking neurons, plastic synapses, delays)
- Timing semantics: `time.mode` (exact_event/fixed_step), resolution, epsilon contracts
- Units: time, voltage, current, dimensionless event values
- Profiles: BASE/REALTIME/etc. to gate features by device profiles
- Probes: deterministic trace capture points

Minimal example:

```json
{
  "version": "0.1.0",
  "profile": "REALTIME",
  "seed": 5,
  "time": { "unit": "us", "mode": "exact_event", "epsilon_time_us": 50, "epsilon_numeric": 1e-5 },
  "graph": { "name": "vision_corner_tracking" },
  "nodes": [
    { "id": "corners", "kind": "kernel", "op": "corner_tracking", "params": { "window_us": 5000 } },
    { "id": "probe_corners", "kind": "probe", "params": { "target": "corners", "type": "custom" } }
  ],
  "edges": [],
  "probes": [
    { "id": "p_corners", "target": "corners", "type": "custom", "window_us": 10000 }
  ]
}
```

Example EIRs:
- Vision corner tracking: [examples/vision_corner_tracking/eir.json](examples/vision_corner_tracking/eir.json)
- Vision object tracking: [examples/vision_object_tracking/eir.json](examples/vision_object_tracking/eir.json)
- Robotics SLAM: [examples/robotics_slam/eir.json](examples/robotics_slam/eir.json)


## Backends and Capability Negotiation

Backends implement deterministic executors:
- CPU simulator: deterministic canonical merge, reference semantics
- GPU simulator: high‑throughput simulation (timing-accurate)
- Vendor plugins: Loihi, SpiNNaker, SynSense, custom ASICs

Device Capability Descriptors (DCD, JSON schema) declare:
- Supported ops, profiles, and precision
- Time resolution and scheduling modes
- Overflow policies, memory constraints
- Emulated ops and tolerance bounds

Planners perform:
- Profile gating and feature substitution
- Time quantization checking vs epsilon contract
- Overflow policy substitution and reporting
- Emulation fallback with declared tolerances

Backend selection:
```bash
# Explicit
ef run --backend cpu-sim ...

# Automatic (negotiation from DCD + EIR requirements)
ef run --backend auto ...
```


## CLI Reference (ef)

Common commands:

```bash
# Validate artifacts (EIR, Event Tensor, DCD, packages)
ef --json validate --eir examples/vision_corner_tracking/eir.json

# Normalize/stream sensor inputs via SAL
ef --json sal-stream --uri "vision.dvs://file?format=jsonl&path=.../input.jsonl" \
  --out out/stream.jsonl --telemetry-out out/telemetry.json

# Compile/plan and run a graph
ef run --eir path/to/eir.json --backend cpu-sim \
  --input out/stream.jsonl --trace-out out/trace.jsonl

# Profile execution
ef profile --eir path/to/eir.json --backend cpu-sim \
  --input out/stream.jsonl --report out/profile.json

# Compare traces (conformance)
ef --json compare-traces --golden path/golden.jsonl \
  --candidate out/trace.jsonl --eps-time-us 50 --eps-numeric 1e-5

# Package for deployment (EFPKG)
ef package --eir path/to/eir.json --capabilities path/device.dcd.json \
  --out out/package.efpkg
```

SAL URI schemes:
- `vision.dvs://file?format=jsonl&path=...`
- `audio.mic://file?path=...&window_ms=20&hop_ms=10&bands=32`
- `imu.6dof://file?path=...`


## Domain Modules and Example Workflows

Vision (event cameras)
- Optical flow, corner detection/tracking, object tracking
- Example:
  ```bash
  ef run --eir examples/vision_object_tracking/eir.json --backend cpu-sim \
    --input examples/vision_optical_flow/traces/inputs/vision_sample.jsonl \
    --trace-out out/vision_object_tracking.trace.jsonl
  ```

Audio (event‑driven audio streams)
- Voice activity detection (VAD), keyword spotting (KWS), diarization, spatial localization
- Example:
  ```bash
  ef --json sal-stream --uri "audio.mic://file?path=examples/wakeword/audio.wav&window_ms=20&hop_ms=10&bands=32" \
      --out out/audio_bands.jsonl --telemetry-out out/audio_bands.telemetry.json
  ef run --eir examples/wakeword/eir.json --backend cpu-sim \
      --input out/audio_bands.jsonl --trace-out out/wakeword.trace.jsonl
  ```

Robotics (IMU/DVS fusion)
- Reflex controllers, event‑based SLAM primitives, obstacle avoidance, adaptive motor control
- Example:
  ```bash
  ef --json sal-stream --uri "imu.6dof://file?path=examples/robotics_slam/traces/inputs/imu_sample.csv" \
     --out out/imu.norm.jsonl --telemetry-out out/imu.telemetry.json
  ef run --eir examples/robotics_slam/eir.json --backend cpu-sim \
     --input out/imu.norm.jsonl --trace-out out/robotics_slam.trace.jsonl
  ```

Additional modules are provided for time series (anomaly detection, change‑point detection, adaptive forecasting), wellness (HRV, sleep segmentation, stress), and creative applications (bio‑adaptive sequencing, event‑reactive graphics). See [eventflow-modules/](eventflow-modules) and the `examples/` directory.


## Development, Conformance, and Tooling

Run tests:

```bash
pytest -q
```

Conformance automation (golden generation, comparisons, badges):

```bash
python tools/ef_conformance.py --out out/conformance
# Produces out/conformance/badges/badges.md and summary JSON
```

Data generators:
- WAV generator: [tools/gen_sine_wav.py](tools/gen_sine_wav.py)
- DVS generator: [tools/gen_dvs_synthetic.py](tools/gen_dvs_synthetic.py)

Example artifacts and goldens are under `examples/**/traces/`.


## Project Structure

- [eventflow-core/](eventflow-core) — runtime engine, EIR, Event Tensor, deterministic operators
- [eventflow-sal/](eventflow-sal) — Sensor Abstraction Layer (DVS, audio, IMU), normalization, telemetry
- [eventflow-backends/](eventflow-backends) — cpu-sim/gpu-sim executors, registry, vendor plugins
- [eventflow-cli/](eventflow-cli) — `ef` CLI: validate, sal-stream, build, run, profile, compare, package
- [eventflow-modules/](eventflow-modules) — domain libraries (vision, audio, robotics, timeseries, wellness, creative)
- [examples/](examples) — end‑to‑end applications and golden traces
- [tools/](tools) — conformance, generators, utilities
- [docs/](docs) — additional documentation
- [tests/](tests) — unit and integration tests


## Troubleshooting

- ef: command not found
  - Ensure `eventflow-cli` is installed (`pip install -e ./eventflow-cli`) and your environment is activated.
- ImportError / missing optional acceleration
  - Install `numpy` to speed up certain SAL paths; core remains deterministic without it.
- Schema validation failed
  - Use `ef --json validate --eir path/to/eir.json` to get precise error locations.
- Backend not available
  - Use `--backend cpu-sim` or install/configure the vendor backend plugin; `--backend auto` will fall back with emulation if possible.
- Trace mismatch in conformance
  - Check `--eps-time-us` and `--eps-numeric` tolerances; confirm identical seeds and input normalization.
- Non‑determinism observed
  - Ensure canonical sort of inputs via SAL (`sal-stream`), disable non‑deterministic device features in planner/profile, confirm fixed seeds.
- Performance issues
  - Try `gpu-sim` if available; profile with `ef profile` to identify hotspots; consider reducing bands/window sizes for audio or spatial resolution for DVS during iteration.


## Contributing




