# EventFlow SDK

EventFlow is a multi-package Python SDK for deterministic, event-driven neuromorphic workflows. The repository includes an EIR graph format, a pure-Python runtime, simulator backends, a sensor abstraction layer, CLI workflows, reference domain modules, package tooling, licensing hooks, and Pro-facing conformance/backend scaffolding.

This README is intentionally candid about the current state. Parts of the repository are usable today for deterministic local pipelines; other parts are API sketches, structured stubs, or benchmark/conformance scaffolds.

## Current Repo State

As of July 9, 2026:

- The reliable path is local Python execution through `eventflow-core`, `eventflow-backends` `cpu-sim`, SAL file/JSONL normalization, and the repo-local CLI.
- The CLI has a real JSON contract and deterministic exit-code behavior, but it depends on editable package installation. Running `eventflow-cli/ef.py` from a bare checkout can fail because package dependencies such as `eventflow-license` are not importable yet.
- Rust native acceleration exists for `eventflow-core` and `eventflow-modules`, but parity and speedup gates only mean something after local `maturin` builds. Without native extensions, native-gated tests can skip or fall back.
- `eventflow-modules` contains many deterministic EIR graph proxies and scaffolds. Treat them as reference building blocks, not finished production algorithms.
- Vendor hardware backends, remote hub operations, live sensor sources, and several interface layers are mostly structured stubs or specifications unless the required SDKs, services, or hardware are supplied.
- Documentation quality is uneven. This root README is the source-of-truth orientation; package READMEs describe package-local reality.

## Distribution Tiers

| Capability | Community | Pro / Internal |
| :--- | :---: | :---: |
| Core runtime and EIR graph support | Yes | Yes |
| CPU simulator path | Yes | Yes |
| Reference domain modules | Yes | Yes |
| Hardware adapter scaffolding | Limited | Yes |
| Actual hardware execution | No default guarantee | Requires SDKs, hardware, and license |
| Conformance/evidence APIs | Basic compare helpers | Pro package scaffolding |
| Audit-grade certification | Not provided by this repo alone | Not complete without external process |

See [Licensing](docs/LICENSING.md) for licensing details.

## Packages

- `eventflow-core`: EIR graph types, validation, serialization, runtime execution, trace helpers, optional Rust kernels.
- `eventflow-sal`: Sensor Abstraction Layer for normalizing file/replay sources into deterministic Event Tensor JSONL plus telemetry.
- `eventflow-backends`: backend registry and simulator implementations; `cpu-sim` is the dependable development target.
- `eventflow-cli`: command-line entrypoint and workflow orchestration; `eventflow-cli/ef.py` is the repo-local launcher.
- `eventflow-modules`: domain module graphs and templates; many modules are proxies/scaffolds rather than full algorithms.
- `eventflow-hub`: local bundle registry and packager; remote hub operations are not implemented.
- `eventflow-license`: signed-license validation utilities used by CLI and Pro gates.
- `eventflow-backends-pro`: proprietary package with vendor adapter scaffolding for Loihi, SpiNNaker, and SynSense.
- `eventflow-conformance`: proprietary package for conformance/evidence scaffolding; not a complete certification system.

## Repository Layout

- `eventflow-core/`: runtime, EIR, conformance compare helpers, optional native extension.
- `eventflow-sal/`: source registry, drivers, stream normalization, timing telemetry.
- `eventflow-backends/`: simulator registry and CPU/GPU/RISC-V-style backend paths.
- `eventflow-cli/`: canonical command handlers and repo-local launcher.
- `eventflow-modules/`: reference domain modules, examples, optional native kernels.
- `eventflow-hub/`: local artifact packaging and registry utilities.
- `eventflow-license/`: license validation and cache support.
- `eventflow-backends-pro/`, `eventflow-conformance/`: Pro/internal packages.
- `examples/`: EIRs, sample inputs, golden traces, and demo scripts.
- `tests/`: unit, integration, and conformance tests.
- `interfaces/`: REST, RPC, and C++ API specifications/partial implementations.
- `tools/`: developer utilities and coverage gates.
- `docs/`: deeper guides, specs, release notes, and audits.

## Source Snapshot

Dated snapshot: July 9, 2026. Counted nonblank lines in source/config/spec files (`.py`, `.rs`, `.proto`, `.sh`, `.toml`, `.yaml`, `.yml`, `.ini`). Excluded build outputs, caches, `target/`, `out/`, pytest scratch data, binaries, docs, and sample data.

| Folder | Files | Physical lines | Nonblank lines |
| :--- | ---: | ---: | ---: |
| `eventflow-modules` | 101 | 13,103 | 10,758 |
| `eventflow-core` | 35 | 3,051 | 2,709 |
| `eventflow-backends` | 26 | 3,074 | 2,539 |
| `eventflow-sal` | 37 | 2,258 | 1,932 |
| `examples` | 15 | 2,166 | 1,794 |
| `tests` | 15 | 1,645 | 1,389 |
| `interfaces` | 4 | 1,447 | 1,295 |
| `eventflow-cli` | 10 | 1,222 | 1,020 |
| `.github` | 6 | 1,070 | 946 |
| `eventflow-backends-pro` | 9 | 682 | 577 |
| `eventflow-hub` | 12 | 601 | 513 |
| `tools` | 5 | 355 | 307 |
| `eventflow-license` | 6 | 244 | 212 |
| `eventflow-conformance` | 5 | 127 | 113 |
| root files | 3 | 56 | 46 |
| **Total** | **289** | **31,101** | **26,150** |

## Quick Start

### 1. Create an environment and install editable packages

Use `python3` to create the venv. After activation, the README commands use `python`, assuming that it resolves to the venv interpreter.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install \
  -e ./eventflow-core \
  -e ./eventflow-sal \
  -e ./eventflow-backends \
  -e ./eventflow-cli \
  -e ./eventflow-modules \
  -e ./eventflow-hub \
  -e ./eventflow-license
```

Optional Pro/internal packages:

```bash
python -m pip install -e ./eventflow-backends-pro -e ./eventflow-conformance
```

### 2. Use the repo-local CLI launcher

From the repository root:

```bash
python eventflow-cli/ef.py --help
```

Optional shell alias:

```bash
alias ef='python eventflow-cli/ef.py'
```

If installed as a script, `eventflow` is also available through the `eventflow-cli` package entrypoint.

## Canonical CLI Workflows

### Discover backends

```bash
python eventflow-cli/ef.py --json list-backends
```

### Validate artifacts

```bash
python eventflow-cli/ef.py --json validate --eir examples/vision_optical_flow/eir.json
python eventflow-cli/ef.py --json validate --event examples/vision_optical_flow/traces/inputs/vision_sample.jsonl
python eventflow-cli/ef.py --json validate --trace examples/vision_optical_flow/traces/golden/vision.golden.jsonl
```

### Vision end-to-end (`sal-stream` -> `build` -> `run` -> `compare-traces`)

```bash
python eventflow-cli/ef.py --json sal-stream \
  --uri "vision.dvs://file?format=jsonl&path=examples/vision_optical_flow/traces/inputs/vision_sample.jsonl" \
  --out out/vision.norm.jsonl \
  --telemetry-out out/vision.telemetry.json

python eventflow-cli/ef.py --json build \
  --eir examples/vision_optical_flow/eir.json \
  --backend cpu-sim \
  --plan-out out/vision.plan.json

python eventflow-cli/ef.py --json run \
  --eir examples/vision_optical_flow/eir.json \
  --backend cpu-sim \
  --input out/vision.norm.jsonl \
  --trace-out out/vision.trace.jsonl \
  --plan out/vision.plan.json

python eventflow-cli/ef.py --json compare-traces \
  --golden examples/vision_optical_flow/traces/golden/vision.golden.jsonl \
  --candidate out/vision.trace.jsonl \
  --eps-time-us 100 \
  --eps-numeric 1e-5
```

### Audio quick flow

```bash
python eventflow-cli/ef.py --json run \
  --eir examples/wakeword/eir.json \
  --backend cpu-sim \
  --input examples/wakeword/traces/inputs/audio_sample.jsonl \
  --trace-out out/wakeword.trace.jsonl
```

### IMU quick flow (`csv` -> SAL -> run)

```bash
python eventflow-cli/ef.py --json sal-stream \
  --uri "imu.6dof://file?path=examples/robotics_slam/traces/inputs/imu_sample.csv" \
  --out out/imu.norm.jsonl \
  --telemetry-out out/imu.telemetry.json

python eventflow-cli/ef.py --json run \
  --eir examples/anomaly_timeseries/eir.json \
  --backend cpu-sim \
  --input out/imu.norm.jsonl \
  --trace-out out/imu.trace.jsonl
```

## Testing

### Fast gate

Run after the editable install above:

```bash
python -m pytest -q -rs
```

Focused suites:

```bash
python -m pytest -q tests/unit -rs
python -m pytest -q tests/integration -rs
python -m pytest -q tests/conformance -rs
python -m pytest -q eventflow-cli/tests -rs
python -m pytest -q eventflow-sal/tests -rs
python -m pytest -q eventflow-backends/tests/test_registry.py -rs
```

### Native/performance gates

These gates require local native builds. Without them, tests can skip or exercise fallback paths rather than validating real speedups.

```bash
python -m pip install -U maturin
(cd eventflow-core && python -m maturin develop -r)
(cd eventflow-modules && python -m maturin develop -r)

EF_NATIVE=1 python -m pytest -q eventflow-core/tests/test_native_parity.py
EF_NATIVE=1 EF_BENCH_GATE=1 CORE_BUCKET_MIN=1.5 CORE_FUSE_MIN=1.5 python -m pytest -q eventflow-core/tests/test_bench_gate_speedups.py
EF_NATIVE=1 EF_BENCH_GATE=1 MOD_PASS_MIN=1.3 MOD_FUSE_MIN=1.5 python -m pytest -q eventflow-modules/tests/test_bench_gate_speedups.py
```

## CI Workflows

- Fast required PR gate: `.github/workflows/ci-fast.yml`
- Manual benchmark workflow: `.github/workflows/bench.yml`
- Manual native parity/perf workflow: `.github/workflows/native-gates.yml`
- Wheel build/release workflows: `.github/workflows/wheels.yml`, `.github/workflows/release.yml`

## CLI Contracts

- Run CLI tests and the repo-local launcher from repo root so path bootstrapping works.
- `--json` means machine-readable output only; commands must not print extra text in JSON mode.
- Exit codes are deterministic: `0` success, `1` validation/conformance/runtime failure, `2` argument or IO usage error.
- Legacy `validate-*` command aliases are removed; use grouped `validate` flags.
- Packaging `build` accepts EIR JSON input only in this version.

## Documentation Map

- `docs/README.md` (index)
- `docs/CLI.md`
- `docs/SAL.md`
- `docs/BACKENDS.md`
- `docs/CONFORMANCE.md`
- `docs/DETERMINISM.md`
- `docs/specs/`
