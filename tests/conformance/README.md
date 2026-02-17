# Conformance Tests

This suite validates `compare-traces` contracts in JSON mode:
- exact match success
- epsilon tolerance violation failure
- malformed trace/header failure
- no extra stdout noise in machine-readable mode

Run:

```bash
python -m pytest -q tests/conformance -rs
```
