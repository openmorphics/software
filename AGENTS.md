# AGENTS.md

This file provides guidance to agents when working with code in this repository.

Non-obvious build/test/run specifics
- eventflow-core native must be built locally before parity/bench “speedup gate” tests will actually run (otherwise they skip silently): cd eventflow-core && python -m pip install -U maturin && python -m maturin develop -r ([pyproject config](eventflow-core/pyproject.toml:29), [Cargo deps](eventflow-core/rust/Cargo.toml:12)).
- Single test (native parity example): EF_NATIVE=1 python -m pytest -q eventflow-core/tests/test_native_parity.py::test_bucket_sum_parity_grouping_and_boundaries ([loader.is_enabled()](eventflow-core/eventflow_core/_rust/__init__.py:60)).
- Bench gate (native required, env-gated): EF_NATIVE=1 EF_BENCH_GATE=1 CORE_BUCKET_MIN=1.5 CORE_FUSE_MIN=1.5 python -m pytest -q eventflow-core/tests/test_bench_gate_speedups.py ([README thresholds](eventflow-core/README.md:96)).
- CLI tests should invoke the repo-local launcher `eventflow-cli/ef.py` from repo root with `--json`; it delegates to canonical parser [`eventflow_cli.main`](eventflow-cli/eventflow_cli/main.py).

Project-specific CLI patterns (do not “simplify”)
- `eventflow-cli/ef.py` is a thin launcher only; command behavior lives in [`eventflow-cli/eventflow_cli/main.py`](eventflow-cli/eventflow_cli/main.py).
- eventflow_cli command handlers intentionally keep lazy imports for heavy dependencies; preserve this pattern when adding new commands.

Error handling and output contracts (tests rely on these)
- CLI must keep deterministic exit codes and dual output modes:
  - 0 success; 1 for validation/conformance failures or runtime errors; 2 for IO/argument errors.
  - `--json` toggles machine-readable output; never print extra text in JSON mode.

Native acceleration toggle (affects behavior and tests)
- EF_NATIVE=1 forces native when importable; warns and falls back if import fails. EF_NATIVE=0 disables native. Unset = auto ([loader](eventflow-core/eventflow_core/_rust/__init__.py:51)).

Scope limits intentionally enforced
- Packaging `build` only accepts EIR JSON input; any Python builder path must error (do not broaden in v0.1).
