# EventFlow Test Suites

- `unit/`: fast module-level and package-level correctness tests.
- `integration/`: end-to-end SAL -> CLI -> backend flows for vision/audio/IMU paths and error contracts.
- `conformance/`: trace-compare behavior and JSON contract checks for deterministic CLI automation.

Run all local tests:

```bash
python -m pytest -q -rs
```

Run focused suites:

```bash
python -m pytest -q tests/integration -rs
python -m pytest -q tests/conformance -rs
python -m pytest -q tests/unit -rs
```

Coverage gates (line + branch, per-package):

```bash
python -m pytest -q -rs \
  --cov=eventflow_core \
  --cov=eventflow_backends \
  --cov=eventflow_cli \
  --cov=eventflow_sal \
  --cov=eventflow_modules \
  --cov=eventflow_hub \
  --cov-branch \
  --cov-report=json:out/coverage.local.json
python tools/check_coverage_gates.py --coverage-json out/coverage.local.json
```
