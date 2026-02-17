# EventFlow

EventFlow is a multi-package SDK for deterministic, event-driven pipelines.
It includes:

- `eventflow-core`: runtime, validators, conformance comparator
- `eventflow-sal`: SAL URI normalization to Event Tensor JSONL
- `eventflow-backends`: backend registry + `cpu-sim` / `gpu-sim`
- `eventflow-cli`: canonical CLI (`eventflow_cli.main`) + thin repo launcher (`eventflow-cli/ef.py`)
- `eventflow-modules`: domain modules and optional native acceleration
- `eventflow-hub`: local package registry utilities

## Repository Layout

- `eventflow-core/`
- `eventflow-sal/`
- `eventflow-backends/`
- `eventflow-cli/`
- `eventflow-modules/`
- `eventflow-hub/`
- `examples/` (EIRs, sample inputs, golden traces)
- `tests/` (unit, integration, conformance)
- `docs/`

## Quick Start

### 1) Create environment and install packages

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ./eventflow-core -e ./eventflow-sal -e ./eventflow-backends -e ./eventflow-cli -e ./eventflow-modules -e ./eventflow-hub
```

### 2) Use the repo-local CLI launcher

From repo root:

```bash
python eventflow-cli/ef.py --help
```

Optional shell alias:

```bash
alias ef='python eventflow-cli/ef.py'
```

If installed as a script, `eventflow` is also available via `eventflow-cli` package entrypoint.

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

### Audio quick flow (sample JSONL)

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

### Fast gate (same scope as required CI)

```bash
python -m pytest -q -rs
```

### Focused suites

```bash
python -m pytest -q tests/unit -rs
python -m pytest -q tests/integration -rs
python -m pytest -q tests/conformance -rs
python -m pytest -q eventflow-cli/tests -rs
python -m pytest -q eventflow-sal/tests -rs
python -m pytest -q eventflow-backends/tests/test_registry.py -rs
```

### Native/performance gates (manual heavy validation)

```bash
python -m pip install -U maturin
(cd eventflow-core && python -m maturin develop -r)
(cd eventflow-modules && python -m maturin develop -r)

EF_NATIVE=1 python -m pytest -q eventflow-core/tests/test_native_parity.py
EF_NATIVE=1 EF_BENCH_GATE=1 CORE_BUCKET_MIN=1.5 CORE_FUSE_MIN=1.5 python -m pytest -q eventflow-core/tests/test_bench_gate_speedups.py
EF_NATIVE=1 EF_BENCH_GATE=1 MOD_PASS_MIN=1.3 MOD_FUSE_MIN=1.5 python -m pytest -q eventflow-modules/tests/test_bench_gate_speedups.py
```

## CI Workflows

- Fast required PR gate (Linux/macOS/Windows): `.github/workflows/ci-fast.yml`
- Manual benchmark workflow: `.github/workflows/bench.yml`
- Manual native parity/perf workflow: `.github/workflows/native-gates.yml`
- Wheel build workflow (release/manual): `.github/workflows/wheels.yml`

## Notes

- Run CLI tests and repo-local launcher from repo root so package path bootstrapping works correctly.
- In `--json` mode, command handlers emit machine-readable JSON without extra human text.
- Legacy `validate-*` command aliases are removed; use grouped `validate` flags.

## Documentation Map

- `docs/README.md` (index)
- `docs/CLI.md`
- `docs/SAL.md`
- `docs/BACKENDS.md`
- `docs/CONFORMANCE.md`
- `docs/DETERMINISM.md`
- `docs/specs/`
