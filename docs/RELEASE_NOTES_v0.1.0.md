# EventFlow v0.1.0 Release Notes

Release date: 2026-02-16
Version: `0.1.0`

## Highlights

- Initial multi-package SDK release:
  - `eventflow-core`
  - `eventflow-sal`
  - `eventflow-backends`
  - `eventflow-cli`
  - `eventflow-modules`
  - `eventflow-hub`
- Installed-artifact runtime smoke testing is now part of CI and release workflow gates.
- Native acceleration parity and benchmark gate coverage are enforced for core and modules.
- CLI JSON contract behavior is covered by regression tests for dependency and runtime failures.

## Packaging and Runtime Contract Fixes

- `eventflow-backends` distribution now includes backend `dcd.json` assets.
- Runtime dependency metadata was corrected:
  - `eventflow-backends` now depends on `eventflow-core`.
  - `eventflow-cli` now depends on `eventflow-core`, `eventflow-sal`, `eventflow-backends`, and `eventflow-hub`.

## CLI Changes

- Grouped `validate` is canonical.
- Legacy `validate-*` aliases are removed.
- `--json` mode remains the machine-readable contract path and keeps deterministic exit-code behavior.

## Security and Compliance Notes

- v0.1 baseline keeps bounded buffers, deterministic ordering, and process isolation defaults.
- Hard sandboxing extensions (for example seccomp/container profiles) are deferred and documented in `docs/SECURITY.md`.

## Known Limitations

- Simulator backends (`cpu-sim`, `gpu-sim`) are the primary validated execution targets for v0.1.
- Vendor backend adapters are intentionally limited baseline integrations in this release.
