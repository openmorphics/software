# EventFlow v0.1.0 Full Release Checklist

Last updated: 2026-02-17
Owner: Release engineering

## Phase 1: Scope Lock

- [ ] Finalize package release scope:
  - [ ] Option A: `eventflow-core` + `eventflow-modules` only
  - [ ] Option B: Full SDK (`eventflow-core`, `eventflow-sal`, `eventflow-backends`, `eventflow-cli`, `eventflow-modules`, `eventflow-hub`)
- [ ] Finalize supported Python versions and OS matrix
- [ ] Freeze release branch and cut candidate commit

## Phase 2: Blocker Fixes

- [x] Add missing runtime dependencies in package metadata:
  - [x] `eventflow-backends` declares `eventflow-core`
  - [x] `eventflow-cli` declares `eventflow-core`, `eventflow-sal`, `eventflow-backends`, `eventflow-hub`
- [x] Include backend JSON resources in distributions:
  - [x] Add setuptools package-data rules for backend `*.json` assets
  - [x] Add `MANIFEST.in` rule for backend JSON assets
- [x] Rebuild artifacts and verify wheel/sdist include required backend `dcd.json` files
- [x] Validate clean-venv install from built artifacts and run:
  - [x] `eventflow --json version`
  - [x] `eventflow --json list-backends`
  - [x] `eventflow --json run --eir ... --backend cpu-sim --input ... --trace-out ...`

### Phase 2 Evidence (2026-02-16)

- Built updated artifacts:
  - `out/release_phase2_artifacts_20260216_185848/eventflow-backends/eventflow_backends-0.1.0-py3-none-any.whl`
  - `out/release_phase2_artifacts_20260216_185848/eventflow-backends/eventflow_backends-0.1.0.tar.gz`
  - `out/release_phase2_artifacts_20260216_185848/eventflow-cli/eventflow_cli-0.1.0-py3-none-any.whl`
  - `out/release_phase2_artifacts_20260216_185848/eventflow-cli/eventflow_cli-0.1.0.tar.gz`
- Verified backend JSON packaging in wheel/sdist (`cpu_sim/gpu_sim/vendor_backends/*/dcd.json` present).
- Verified wheel dependency metadata:
  - `eventflow-backends` requires `eventflow-core`.
  - `eventflow-cli` requires `eventflow-core`, `eventflow-sal`, `eventflow-backends`, `eventflow-hub`.
- Clean venv smoke:
  - Venv: `out/release_phase2_venv_20260216_185848`
  - `eventflow --json version` => RC 0
  - `eventflow --json list-backends` => RC 0
  - `eventflow --json run ... --backend cpu-sim ...` => RC 0
  - Trace output: `out/release_phase2_smoke.trace.jsonl`

## Phase 3: CI and Release Workflow Completion

- [x] Align release workflows with chosen package scope
- [x] Add installed-artifact smoke tests to CI (not editable installs)
- [x] Require wheel/sdist runtime smoke before publish

### Phase 3 Evidence (2026-02-16)

- Updated `.github/workflows/release.yml`:
  - Added `build-python-packages` job for `eventflow-sal`, `eventflow-backends`, `eventflow-cli`, `eventflow-hub`.
  - Added `test-artifacts` job that installs built artifacts in a clean venv and runs CLI runtime smoke commands.
  - Gated `publish` on `test-artifacts` and added `twine check` before publish.
- Updated `.github/workflows/wheels.yml`:
  - Added `build-python-packages` job.
  - Extended `test-wheels` to install compatible wheels only and run installed-artifact CLI/runtime smoke tests.
- Updated `.github/workflows/ci-fast.yml`:
  - Added `artifact-smoke (linux)` job that builds wheels for all packages and executes installed-artifact smoke tests.
- Verified workflow YAML parse for all workflow files.

## Phase 4: Test and Quality Hardening

- [x] Keep fast gate green (`pytest -q -rs`)
- [x] Keep native gates green
- [x] Add tests for packaged backend resource loading
- [x] Add tests for CLI dependency/runtime import contracts

### Phase 4 Evidence (2026-02-16)

- Added backend packaged-resource tests:
  - `eventflow-backends/tests/test_packaged_resources.py`
  - Verifies `dcd.json` loadability via `importlib.resources` for built-in and vendor backends.
  - Verifies built-in backend loader succeeds with packaged DCD assets.
- Added CLI dependency/runtime contract tests:
  - `eventflow-cli/tests/test_cli_dependency_contracts.py`
  - Verifies dependency import failures emit JSON error payloads and deterministic exit code `2`.
- Added runtime contract regression case:
  - `eventflow-cli/tests/test_ef_cli_json.py` (`test_run_unknown_backend_returns_runtime_contract`)
  - Verifies unknown backend emits JSON runtime failure and deterministic exit code `1`.
- Validation runs:
  - `python3 -m pytest -q -rs` => `207 passed, 4 skipped, 5 subtests passed`
  - `EF_NATIVE=1 python3 -m pytest -q eventflow-core/tests/test_native_parity.py -rs` => `16 passed`
  - `EF_NATIVE=1 EF_BENCH_GATE=1 CORE_BUCKET_MIN=1.5 CORE_FUSE_MIN=1.5 python3 -m pytest -q eventflow-core/tests/test_bench_gate_speedups.py -rs` => `2 passed`
  - `EF_NATIVE=1 EF_BENCH_GATE=1 MOD_PASS_MIN=1.3 MOD_FUSE_MIN=1.5 python3 -m pytest -q eventflow-modules/tests/test_bench_gate_speedups.py -rs` => `2 passed`

### Phase 4 Addendum (2026-02-17)

- Added per-package and overall coverage gate enforcement:
  - `tools/coverage_gates.json`
  - `tools/check_coverage_gates.py`
  - `.github/workflows/ci-fast.yml` runs coverage+gate check on Linux matrix leg.
- Added coverage-hardening regression tests for high-risk paths:
  - `tests/unit/test_sal_registry_dispatch.py`
  - `tests/unit/test_sal_driver_smoke.py`
  - `tests/unit/test_modules_risk_paths.py`
  - `tests/unit/test_hub_registry_client_extra.py`
  - `tests/integration/test_cli_additional_contracts.py`
- Full-suite coverage validation:
  - `python3 -m pytest -q -rs --cov=eventflow_core --cov=eventflow_backends --cov=eventflow_cli --cov=eventflow_sal --cov=eventflow_modules --cov=eventflow_hub --cov-branch --cov-report=json:out/coverage_gate_run_20260216_230403/coverage.json --cov-report=xml:out/coverage_gate_run_20260216_230403/coverage.xml`
  - `python3 tools/check_coverage_gates.py --coverage-json out/coverage_gate_run_20260216_230403/coverage.json`
  - Result: `255 passed, 5 skipped, 5 subtests passed`; coverage gates `PASSED`.
- Module robustness hardening and compatibility closure:
  - Added comprehensive domain module contract tests:
    - `eventflow-modules/tests/test_domain_module_contracts.py`
  - Added core compatibility and utility tests:
    - `eventflow-core/tests/test_graph_compat_and_utils.py`
  - Hardened compatibility/runtime surfaces:
    - `eventflow-core/eventflow_core/eir/graph.py`
    - `eventflow-core/eventflow_core/eir/ops.py`
    - `eventflow-core/eventflow_core/runtime/scheduler.py`
    - `eventflow-core/eventflow_core/eir/serialize.py`
  - Fixed module-level robustness defects:
    - `eventflow-modules/eventflow_modules/industrial/predictive_maintenance.py`
    - `eventflow-modules/eventflow_modules/industrial/quality_control.py`
    - `eventflow-modules/eventflow_modules/smart_agriculture/crop_monitoring.py`
    - `eventflow-modules/eventflow_modules/smart_agriculture/agricultural_automation.py`
    - `eventflow-modules/eventflow_modules/smart_agriculture/environmental_monitoring.py`
    - `eventflow-modules/eventflow_modules/scientific_research/data_analysis.py`
    - `eventflow-modules/eventflow_modules/wellness/sleep.py`
    - `eventflow-modules/eventflow_modules/wellness/stress.py`
  - Validation runs:
    - `python3 -m pytest -q -rs eventflow-modules/tests` => `124 passed, 2 skipped`
    - `python3 -m pytest -q -rs` => `329 passed, 5 skipped, 5 subtests passed`
    - `python3 -m pytest -q -rs --cov=eventflow_core --cov=eventflow_backends --cov=eventflow_cli --cov=eventflow_sal --cov=eventflow_modules --cov=eventflow_hub --cov-branch --cov-report=json:out/coverage_gate_run_20260217_000012/coverage.json --cov-report=xml:out/coverage_gate_run_20260217_000012/coverage.xml`
    - `python3 tools/check_coverage_gates.py --coverage-json out/coverage_gate_run_20260217_000012/coverage.json` => coverage gates `PASSED`

## Phase 5: Release Documentation and Compliance

- [x] Add `CHANGELOG.md` for v0.1.0
- [x] Finalize release notes and migration notes
- [x] Close `docs/SECURITY.md` v0.1 `TBD` items or document accepted deferral

### Phase 5 Evidence (2026-02-17)

- Added release changelog:
  - `CHANGELOG.md`
- Added release documentation:
  - `docs/RELEASE_NOTES_v0.1.0.md`
  - `docs/MIGRATION_v0.1.0.md`
- Closed security `TBD` by documenting v0.1 accepted deferral for advanced kernel hardening:
  - `docs/SECURITY.md`
- Added docs index links for release artifacts:
  - `docs/README.md`

## Phase 6: TestPyPI Rehearsal

- [ ] Publish candidate artifacts to TestPyPI from release workflow
- [ ] Install from TestPyPI in fresh environments
- [x] Execute end-to-end CLI smoke flows

### Phase 6 Evidence (2026-02-17)

- Built candidate wheels/sdists for full SDK and verified metadata integrity:
  - Artifacts: `out/release_phase6_artifacts_20260216_201516/all`
  - Verification: `python3 -m twine check out/release_phase6_artifacts_20260216_201516/all/*` => all passed
- TestPyPI publish attempt (credential-gated) is currently blocked in this environment:
  - Command: `python3 -m twine upload --repository-url https://test.pypi.org/legacy/ --skip-existing -u __token__ -p "$TEST_PYPI_API_TOKEN" out/release_phase6_artifacts_20260216_201516/all/*`
  - Result: `HTTPError: 403 Forbidden`
  - Environment status: `TEST_PYPI_API_TOKEN` unset, `gh` CLI unavailable, `~/.pypirc` absent
- Fresh-venv install from TestPyPI remains blocked until publish credentials are provided:
  - Log: `out/release_phase6_testpypi_install_20260216_201646.log`
  - Result: `No matching distribution found for eventflow-cli==0.1.0`
- End-to-end CLI smoke completed in a fresh artifact-installed environment:
  - Venv: `out/release_phase6_local_venv_20260216_201635`
  - Outputs: `out/release_phase6_smoke/wakeword.trace.jsonl`, `out/release_phase6_smoke/wakeword.compare.json`, `out/release_phase6_smoke/summary.json`
  - Commands validated: `eventflow --json version`, `eventflow --json list-backends`, `eventflow --json run ...`, `eventflow --json compare-traces ...`
- License metadata deprecation risk cleared:
  - Updated all package `pyproject.toml` files to use SPDX string license metadata and removed deprecated license classifiers.
  - Verification build log (no matching deprecation warnings): `out/release_phase6_licensecheck_20260216_202052/build.log`
  - Verification artifacts (`twine check` passed): `out/release_phase6_licensecheck_20260216_202052/all`
- Runtime deprecation warning risk reduced in hub registry:
  - Updated `eventflow-hub/eventflow_hub/registry.py` to use timezone-aware UTC timestamps (`datetime.now(timezone.utc)`), replacing deprecated `datetime.utcnow()`.

## Phase 7: Production Release

- [ ] Tag release
- [ ] Publish to PyPI
- [ ] Run post-publish verification
- [ ] Record final release report and rollback notes

## Exit Criteria (GO)

- [x] All Phase 2 blockers closed
- [ ] Required CI workflows green on release commit
- [x] Artifact-only install/run verified
- [x] Release docs complete for shipped scope
