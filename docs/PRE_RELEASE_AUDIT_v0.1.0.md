# EventFlow v0.1.0 — Pre‑Release Audit and Finalization

This document is the formal, point‑by‑point audit for the v0.1.0 pre‑release, covering documentation/API consistency, test coverage, code quality, system integration, security, and release preparation. It consolidates the release notes, migration guidance, deployment checklist, and troubleshooting playbooks to ensure a production‑ready baseline.

Sections
- Executive Summary
- Documentation and API Consistency Review
- Test Coverage and Quality Assurance
- Code Quality and Maintenance
- System Integration and Compatibility
- Security and Deployment Readiness
- Release Preparation
  - Release Notes
  - Migration Guide
  - Deployment Checklist
  - Troubleshooting Guide
- Appendix: Inventory of Updated/Key Artifacts


## Executive Summary

Scope accomplished in this pre‑release:
- CLI JSON mode implemented and documented; tests added for version, list‑backends, compare‑traces, SAL passthrough and end‑to‑end run.
- SAL timestamp normalization augmented with drift/jitter estimation and dt percentiles; registry improved for file/device URIs with defensive errors.
- Deterministic scheduler modes (exact_event and fixed_step) finalized and tested in core runtime.
- Docs synchronized across CLI, SAL, backends, and top‑level project READMEs; deployment and conformance flows clarified.
- Integration smoke tests and JSON output smoke tests added; run/profile/compare flows validated on example assets.

Known limitations (tracked for minor follow‑up):
- Vendor backends remain structured stubs; planning/execution is validated through cpu‑sim/gpu‑sim reference implementations.
- API docstrings coverage is high for SAL and core runtime paths; CLI subcommands (ef) are primarily documented through docs and tests, with inline docstrings slated for v0.1.1 polish.


## Documentation and API Consistency Review

Updated docs and READMEs reflect:
- CLI JSON output mode and command shape changes:
  - [docs/CLI.md](docs/CLI.md)
  - [eventflow-cli/README.md](eventflow-cli/README.md)
- SAL timestamp handling: drift/jitter stats and dt percentiles; JSONL passthrough normalization:
  - [docs/SAL.md](docs/SAL.md)
  - [eventflow-sal/README.md](eventflow-sal/README.md)
  - High‑level SAL function: [stream_to_jsonl()](eventflow-sal/api.py:171)
- Backend registry and execution planning behaviors:
  - [docs/BACKENDS.md](docs/BACKENDS.md)
- Deterministic modes and conformance:
  - [docs/DETERMINISM.md](docs/DETERMINISM.md)
  - [docs/CONFORMANCE.md](docs/CONFORMANCE.md)
- Top‑level README aligned to current architecture, installation, and example workflows:
  - [README.md](README.md)
  - [docs/README.md](docs/README.md)

Public API docstrings status (spot‑check):
- SAL: [stream_to_jsonl()](eventflow-sal/api.py:171) includes detailed docstring and parameters.
- Core runtime: [run_event_mode()](eventflow-core/eventflow_core/runtime/exec.py:1) and [run_fixed_dt()](eventflow-core/eventflow_core/runtime/exec.py:25) include docstrings in the synchronized draft; tests exercise semantics.
- CLI ef subcommands primarily documented in [docs/CLI.md](docs/CLI.md); inline function docstrings are planned to be added to ef subcommand handlers in a subsequent patch (v0.1.1) without breaking interfaces.

Architectural diagrams and flows:
- Updated textual pipeline diagrams and file flow in [README.md](README.md) and [docs/CLI.md](docs/CLI.md).

Installation instructions:
- Synchronized versions and prerequisites across [README.md](README.md) and [docs/README.md](docs/README.md) (Python 3.9+ for the SDK, optional numpy).


## Test Coverage and Quality Assurance

New/updated tests:
- CLI JSON smoke tests:
  - [eventflow-cli/tests/test_ef_cli_json.py](eventflow-cli/tests/test_ef_cli_json.py)
  - [eventflow-cli/tests/test_ef_cli_sal_and_run.py](eventflow-cli/tests/test_ef_cli_sal_and_run.py)
- SAL normalization and telemetry:
  - [eventflow-sal/tests/test_stream_jsonl.py](eventflow-sal/tests/test_stream_jsonl.py)
- Core schedulers determinism:
  - [eventflow-core/tests/test_scheduler_modes.py](eventflow-core/tests/test_scheduler_modes.py)

Existing tests exercised in regression pass:
- SAL packet parsing, URI parsing, replay stub:
  - [eventflow-sal/tests/test_packet.py](eventflow-sal/tests/test_packet.py)
  - [eventflow-sal/tests/test_uri.py](eventflow-sal/tests/test_uri.py)
  - [eventflow-sal/tests/test_replay.py](eventflow-sal/tests/test_replay.py)
- Core ops and runtime behavior:
  - [eventflow-core/tests/test_ops_audio.py](eventflow-core/tests/test_ops_audio.py)
  - [eventflow-core/tests/test_ops_xy.py](eventflow-core/tests/test_ops_xy.py)
  - [eventflow-core/tests/test_ops_lif.py](eventflow-core/tests/test_ops_lif.py)
  - [eventflow-core/tests/test_graph_exec_event.py](eventflow-core/tests/test_graph_exec_event.py)

Coverage guidance:
- Recommended: use pytest-cov locally for a pre‑release gate:
  - python
    python -m pip install pytest pytest-cov
    pytest --maxfail=1 -q --cov=eventflow_core --cov=eventflow_sal --cov=eventflow_backends --cov=eventflow_cli --cov-report=term-missing

Data integrity and reproducibility:
- SAL passthrough normalization preserves header and ordering; telemetry captures dt percentiles and jitter; JSON output mode for compare‑traces validates end‑to‑end equivalence deterministically.


## Code Quality and Maintenance

Cleanup and formatting:
- Imports reviewed/trimmed in touched modules; no debug prints in hot paths.
- Errors standardized with friendly codes/messages in SAL registry:
  - [resolve_source()](eventflow-sal/eventflow_sal/registry.py:14)
- Style guidance:
  - PEP 8 recommended; adopt black/isort/flake8 in CI (post‑0.1.0).
- Error handling:
  - ef CLI subcommands report actionable messages and set non‑zero exit codes on failure (validators, sal‑stream, compare‑traces).


## System Integration and Compatibility

Interoperability validation:
- CLI → SAL normalization → cpu‑sim run → trace compare flows validated in tests.
- Backends:
  - Registry discovery and planning in simulators verified; vendor stubs left as future work.
- Serialization/deserialization:
  - Event Tensor JSONL headers enforced and present; compare‑traces consumes both streams deterministically.
- Resource behavior:
  - SAL paths close files promptly; run pipelines write outputs under specified paths.
- Cross‑platform:
  - Development and tests target macOS/Linux + Python 3.9+; Windows via WSL recommended.

Performance notes:
- gpu‑sim provides deterministic trace emission analogous to cpu‑sim; performance characteristics to be improved in minor versions.


## Security and Deployment Readiness

Input validation and file handling:
- SAL passthrough normalization verifies headers and ensures deterministic ordering; JSONL direct open() is disallowed with a descriptive error to prevent bypass of normalization:
  - [resolve_source()](eventflow-sal/eventflow_sal/registry.py:23)

Configuration handling:
- CLI arguments sanitized via argparse; ef uses restricted file IO with explicit paths.

Logging:
- CLI JSON outputs omit sensitive environment details; telemetry strictly includes timing and counter data.

Sandboxing (baseline):
- Security policy stubs referenced in docs; untrusted kernel execution is not enabled in this baseline.


## Release Preparation

### Release Notes (v0.1.0)

Highlights
- Deterministic runtime
  - exact_event and fixed_step schedulers with tests: [test_scheduler_modes.py](eventflow-core/tests/test_scheduler_modes.py)
- SAL
  - JSONL passthrough normalization with header enforcement: [stream_to_jsonl()](eventflow-sal/api.py:171)
  - Drift/jitter estimation and dt percentiles in telemetry
  - Defensive registry errors; file/device URI handling: [registry.py](eventflow-sal/eventflow_sal/registry.py)
- Backends
  - cpu‑sim/gpu‑sim planning and deterministic trace emission: [executor.py (cpu)](eventflow-backends/cpu_sim/executor.py:1), [executor.py (gpu)](eventflow-backends/gpu_sim/executor.py:1)
- CLI
  - JSON output mode for version, list‑backends, sal‑stream, compare‑traces, package: [ef.py](eventflow-cli/ef.py)
  - New profiling stats for Event Tensor JSONL
- Docs
  - Synchronized CLI/SAL/Backends specs: [docs/CLI.md](docs/CLI.md), [docs/SAL.md](docs/SAL.md), [docs/BACKENDS.md](docs/BACKENDS.md)
  - Project overviews: [README.md](README.md), [docs/README.md](docs/README.md)

Breaking changes
- SAL: JSONL inputs must be normalized via stream_to_jsonl (vision.dvs://file?format=jsonl&path=...), not opened directly via SAL open(); attempting to open JSONL raises a standardized error.
- CLI: Preferred backend names in ef are hyphenated (cpu‑sim, gpu‑sim) matching the backend registry; older underscore style (cpu_sim) remains in the legacy eventflow_cli examples only.

Deprecations
- Direct JSONL driver open() flows are deprecated in favor of SAL normalization to ensure deterministic behavior and consistent telemetry.

Known issues
- Vendor backends are placeholder stubs; use simulators for development and conformance.


### Migration Guide (to v0.1.0)

1) SAL usage
- Before: Some flows read JSONL directly.
- Now: Normalize via SAL:
  - bash
    ef --json sal-stream --uri "vision.dvs://file?format=jsonl&path=path/to/events.jsonl" --out out/stream.jsonl --telemetry-out out/telemetry.json

2) Backend identifiers
- Use hyphenated names with ef: cpu‑sim, gpu‑sim.
  - bash
    ef run --eir path/to/eir.json --backend cpu-sim --input out/stream.jsonl --trace-out out/trace.jsonl

3) CLI JSON output
- Add --json to produce machine‑readable outputs for automation in CI (validators, sal‑stream, compare‑traces, package).

4) Examples
- Use provided examples and generators:
  - [examples/vision_optical_flow/eir.json](examples/vision_optical_flow/eir.json)
  - [tools/gen_dvs_synthetic.py](tools/gen_dvs_synthetic.py)
  - [tools/gen_sine_wav.py](tools/gen_sine_wav.py)


### Deployment Checklist

- Schema validation
  - [ ] EIR JSON validates: ef validate-eir --path model.eir.json
  - [ ] Inputs validate (Event Tensor JSON/JSONL)
  - [ ] DCD validates for target backends

- SAL normalization and telemetry
  - [ ] All recorded inputs normalized via sal‑stream; telemetry archived
  - [ ] dt percentiles and jitter within expected ranges

- Planning and run
  - [ ] Plan generated (build) for selected backend(s)
  - [ ] Golden run captured with seed and hashes
  - [ ] Candidate runs for each target backend complete

- Conformance
  - [ ] compare‑traces PASS within epsilons (time, numeric)
  - [ ] Same‑backend reproducibility (bit‑exact)

- Packaging
  - [ ] EFPKG manifest created (eir, traces, inputs hashes)
  - [ ] Version metadata and compatibility matrices recorded

- Security
  - [ ] No JSONL direct open() bypass; SAL normalization enforced
  - [ ] Inputs validated with schema and bounds

- CI/CD
  - [ ] Unit/integration tests pass with coverage gate
  - [ ] CLI JSON outputs consumed by CI for artifacts/metrics


### Troubleshooting Guide (Summary)

- ef: command not found
  - Ensure eventflow‑cli is installed: pip install -e ./eventflow-cli

- SAL produces no events
  - Verify file extension and URI scheme; use sal‑stream for JSONL inputs

- Conformance mismatch
  - Confirm identical seeds
  - Check epsilons (time/numeric)
  - Validate inputs and ensure SAL ordering

- Backend unavailable
  - Use cpu‑sim/gpu‑sim; vendor plugins require their SDK stacks

- Performance shortfalls
  - Profile with ef profile on inputs; reduce resolution/window sizes for iteration


## Appendix: Inventory of Updated/Key Artifacts

- Runtime and schedulers:
  - [run_event_mode()](eventflow-core/eventflow_core/runtime/exec.py:1)
  - [run_fixed_dt()](eventflow-core/eventflow_core/runtime/exec.py:25)
- SAL normalization/telemetry:
  - [stream_to_jsonl()](eventflow-sal/api.py:171)
  - [resolve_source()](eventflow-sal/eventflow_sal/registry.py:14)
- Simulators:
  - [cpu-sim executor](eventflow-backends/cpu_sim/executor.py:1)
  - [gpu-sim executor](eventflow-backends/gpu_sim/executor.py:1)
- CLI:
  - [ef CLI](eventflow-cli/ef.py)
  - Tests: [test_ef_cli_json.py](eventflow-cli/tests/test_ef_cli_json.py), [test_ef_cli_sal_and_run.py](eventflow-cli/tests/test_ef_cli_sal_and_run.py)
- Docs:
  - [CLI](docs/CLI.md), [SAL](docs/SAL.md), [Backends](docs/BACKENDS.md), [Determinism](docs/DETERMINISM.md), [Conformance](docs/CONFORMANCE.md), [Project README](README.md), [Docs README](docs/README.md)
