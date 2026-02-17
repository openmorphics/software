# Installation

## Requirements

- Python 3.9+
- macOS, Linux, or Windows (WSL recommended)

## Editable Install (Recommended)

```bash
git clone https://github.com/openmorphics/software.git
cd software

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ./eventflow-core -e ./eventflow-sal -e ./eventflow-backends -e ./eventflow-cli -e ./eventflow-modules -e ./eventflow-hub
```

## Verify

Use repo-local launcher:

```bash
python eventflow-cli/ef.py --help
```

Or installed script:

```bash
eventflow --help
```

## Optional Dependencies

```bash
python -m pip install numpy
python -m pip install scipy
```

## Native Build (Manual)

Core:

```bash
python -m pip install -U maturin
cd eventflow-core
python -m maturin develop -r
```

Modules:

```bash
cd eventflow-modules
python -m maturin develop -r
```

## Fast Test Gate

```bash
python -m pytest -q -rs
```

## Manual Native/Perf Validation

```bash
EF_NATIVE=1 python -m pytest -q eventflow-core/tests/test_native_parity.py
EF_NATIVE=1 EF_BENCH_GATE=1 CORE_BUCKET_MIN=1.5 CORE_FUSE_MIN=1.5 python -m pytest -q eventflow-core/tests/test_bench_gate_speedups.py
EF_NATIVE=1 EF_BENCH_GATE=1 MOD_PASS_MIN=1.3 MOD_FUSE_MIN=1.5 python -m pytest -q eventflow-modules/tests/test_bench_gate_speedups.py
```
