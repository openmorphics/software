# Integration Tests

This suite executes real end-to-end CLI pipelines through the repo-local launcher
`eventflow-cli/ef.py` with `--json` contracts.

Coverage includes:
- vision flow: `sal-stream` -> `build` -> `run` -> `compare-traces`
- audio flow: WAV generation (or fixture fallback) -> `sal-stream`/`run` -> `compare-traces`
- IMU flow: CSV -> `sal-stream` -> `run` -> `compare-traces`
- negative contracts: unknown backend, invalid SAL URI/file, compare mismatch

Run:

```bash
python -m pytest -q tests/integration -rs
```
