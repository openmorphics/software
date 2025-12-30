# AGENTS.md

This file provides guidance to agents when working with code in this repository.

Non-obvious build/test/run specifics
- eventflow-core native must be built locally before parity/bench “speedup gate” tests will actually run (otherwise they skip silently): cd eventflow-core && python -m pip install -U maturin && python -m maturin develop -r ([pyproject config](eventflow-core/pyproject.toml:29), [Cargo deps](eventflow-core/rust/Cargo.toml:12)).
- Single test (native parity example): EF_NATIVE=1 python -m pytest -q eventflow-core/tests/test_native_parity.py::test_bucket_sum_parity_grouping_and_boundaries ([loader.is_enabled()](eventflow-core/eventflow_core/_rust/__init__.py:60)).
- Bench gate (native required, env-gated): EF_NATIVE=1 EF_BENCH_GATE=1 CORE_BUCKET_MIN=1.5 CORE_FUSE_MIN=1.5 python -m pytest -q eventflow-core/tests/test_bench_gate_speedups.py ([README thresholds](eventflow-core/README.md:96)).
- CLI tests must invoke the repo-local ef.py from repo root with --json; they do not call the installed console script: python -m pytest -q eventflow-cli/tests/test_ef_cli_json.py::TestEfCliJson::test_compare_traces_json ([spawner](eventflow-cli/tests/test_ef_cli_json.py:12), [ef main()](eventflow-cli/ef.py:590)).

Project-specific CLI patterns (do not “simplify”)
- ef.py dynamically loads sibling packages from repo paths to avoid packaging churn; running outside repo root breaks loaders ([validators loader](eventflow-cli/ef.py:85), [SAL loader](eventflow-cli/ef.py:97), [backend registry loader](eventflow-cli/ef.py:109), [comparator loader](eventflow-cli/ef.py:121)).
- eventflow_cli subcommands intentionally use lazy imports to avoid hard deps during parse; preserve this when adding code ([run.handle()](eventflow-cli/eventflow_cli/run.py:4), [build.handle()](eventflow-cli/eventflow_cli/build.py:4), [validate.handle()](eventflow-cli/eventflow_cli/validate.py:4)).

Error handling and output contracts (tests rely on these)
- ef.py must keep deterministic exit codes and dual output modes:
  - 0 success; 1 for validation/conformance failures or runtime errors; 2 for IO/argument errors ([validators exit paths](eventflow-cli/ef.py:199), [trace validation](eventflow-cli/ef.py:257), [profile errors](eventflow-cli/ef.py:393), [backend run](eventflow-cli/ef.py:563), [compare-traces](eventflow-cli/ef.py:580)).
  - --json toggles machine-readable output via global CLI_JSON; never print extra text in JSON mode ([printer](eventflow-cli/ef.py:139), [flag handling](eventflow-cli/ef.py:682)).

Native acceleration toggle (affects behavior and tests)
- EF_NATIVE=1 forces native when importable; warns and falls back if import fails. EF_NATIVE=0 disables native. Unset = auto ([loader](eventflow-core/eventflow_core/_rust/__init__.py:51)).

Scope limits intentionally enforced
- Packaging “build” in eventflow_cli.build only accepts .eir JSON; any Python builder path must error (do not broaden in v0.1) ([builder rule](eventflow-cli/eventflow_cli/build.py:13)).