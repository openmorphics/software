# EventFlow Core

`eventflow-core` is the runtime and EIR package. It is one of the more substantial parts of the repository: graph types, operators, validation, serialization, event-mode execution, scheduling, trace helpers, conformance comparison helpers, and optional Rust acceleration all live here.

The pure-Python path is the baseline. Native acceleration is optional and must be built or installed before native parity/performance claims are meaningful.

## Current State

- Working today: EIR graph construction, core ops, validation, runtime execution, scheduler modes, trace output, and conformance comparison utilities.
- Optional native extension: Rust kernels are exposed through `eventflow_core._rust._native` when importable.
- Honest limitation: native tests and speedup gates do not prove anything unless the native extension has been built in the active environment.
- Scope boundary: this package is the runtime core, not hardware execution and not a full domain algorithm library.

## Installation

From a released wheel:

```bash
python -m pip install eventflow-core
```

For local development from the repository root:

```bash
python -m pip install -e ./eventflow-core
```

To force a local release-mode native build:

```bash
python -m pip install -U maturin
cd eventflow-core
python -m maturin develop -r
```

## Native Acceleration

`EF_NATIVE` controls whether the Rust extension is used:

- `EF_NATIVE=1`: force native if importable; warn and fall back if import fails.
- `EF_NATIVE=0`: disable native and use pure Python.
- unset: auto-detect native and use it when available.

Examples:

```bash
EF_NATIVE=1 python -c "import eventflow_core._rust as r; print(r.is_enabled())"
EF_NATIVE=0 python -c "import eventflow_core._rust as r; print(r.is_enabled())"
```

Programmatic check:

```python
from eventflow_core._rust import is_enabled

if is_enabled():
    print("native active")
```

## Exceptions and Logging

Use canonical exceptions from `eventflow_core.errors`. They alias to native exception classes when native is loaded, so callers can catch one type regardless of backend:

```python
from eventflow_core.errors import BucketError, FuseError
```

The native module also exposes a minimal synchronous logging bridge:

```python
from eventflow_core._rust import native, set_log_sink

def sink(level, message):
    print(f"[{level}] {message}")

set_log_sink(sink)
native.log_emit("INFO", "hello from native")
set_log_sink(None)
```

Compute-heavy native paths generally avoid logging. Logging callbacks must run while the GIL is held.

## Tests and Gates

Pure Python/core tests:

```bash
python -m pytest -q eventflow-core/tests -rs
```

Native parity and speedup gates:

```bash
python -m pip install -U maturin
(cd eventflow-core && python -m maturin develop -r)

EF_NATIVE=1 python -m pytest -q eventflow-core/tests/test_native_parity.py
EF_NATIVE=1 EF_BENCH_GATE=1 CORE_BUCKET_MIN=1.5 CORE_FUSE_MIN=1.5 \
  python -m pytest -q eventflow-core/tests/test_bench_gate_speedups.py
```

Benchmark-only run:

```bash
python -m pip install -U pytest pytest-benchmark
python -m pytest -q eventflow-core/tests/test_bench_native.py -k bench --benchmark-only --benchmark-autosave
```

## Release Notes for Maintainers

Release workflows target abi3 wheels for Python 3.8+ across macOS universal2, manylinux/musllinux, and Windows MSVC. Treat this as CI/release configuration, not proof that every local checkout has native acceleration available.
