# Changelog

All notable changes to this repository are documented in this file.

## [0.1.0] - 2026-02-16

### Added

- Multi-package SDK release structure:
  - `eventflow-core`
  - `eventflow-sal`
  - `eventflow-backends`
  - `eventflow-cli`
  - `eventflow-modules`
  - `eventflow-hub`
- Canonical CLI command surface in `eventflow-cli/eventflow_cli/main.py`.
- JSON output mode for automation across key CLI commands.
- Deterministic scheduler mode coverage (`exact_event`, `fixed_step`) in core tests.
- Native acceleration parity and benchmark gate coverage for core and modules.
- Installed-artifact smoke validation in CI and release workflows.

### Changed

- CLI validation now uses grouped `validate` target flags instead of legacy alias commands.
- SAL normalization flows are aligned on URI-based streaming to Event Tensor JSONL.
- Release workflows now validate runtime behavior from built artifacts before publish.

### Fixed

- Distribution packaging for `eventflow-backends` now includes required JSON resources (`dcd.json`) for built-in and vendor backend descriptors.
- Runtime dependency metadata added:
  - `eventflow-backends` now depends on `eventflow-core`.
  - `eventflow-cli` now depends on `eventflow-core`, `eventflow-sal`, `eventflow-backends`, and `eventflow-hub`.
- Added regression tests for packaged backend resource loading and CLI dependency error contracts.

### Breaking Changes

- Legacy `validate-*` CLI aliases are removed; use `validate` with one explicit target flag.
- SAL direct JSONL open flows are not part of the canonical path; normalize inputs via `sal-stream`.

### Deprecations

- Direct JSONL driver open workflows are deprecated in favor of SAL normalization.

### Security

- v0.1 baseline ships with bounded-buffer enforcement, deterministic ordering, and no dynamic kernel execution enabled by default.
- Hard isolation features beyond process-level separation are documented as deferred work.

### Known Limitations

- Vendor backend integrations are structured placeholders; simulator backends (`cpu-sim`, `gpu-sim`) are the reference execution targets for v0.1.
