# EventFlow CLI

Canonical CLI package for EventFlow.

- Canonical implementation: `eventflow-cli/eventflow_cli/main.py`
- Repo-local launcher: `eventflow-cli/ef.py` (thin delegate)
- Installed script: `eventflow`

## Local Usage

From repository root:

```bash
python eventflow-cli/ef.py --help
```

## Command Surface

- `version`
- `list-backends`
- `validate`
- `sal-stream`
- `profile`
- `trace-stats`
- `package`
- `build`
- `run`
- `compare-traces`
- `hub`

Use `--json` for machine-readable output.

## Core Examples

```bash
python eventflow-cli/ef.py --json list-backends

python eventflow-cli/ef.py --json validate --eir examples/vision_optical_flow/eir.json

python eventflow-cli/ef.py --json build \
  --eir examples/vision_optical_flow/eir.json \
  --backend cpu-sim \
  --plan-out out/vision.plan.json

python eventflow-cli/ef.py --json run \
  --eir examples/vision_optical_flow/eir.json \
  --backend cpu-sim \
  --input examples/vision_optical_flow/traces/inputs/vision_sample.jsonl \
  --trace-out out/vision.trace.jsonl

python eventflow-cli/ef.py --json compare-traces \
  --golden examples/vision_optical_flow/traces/golden/vision.golden.jsonl \
  --candidate out/vision.trace.jsonl
```

## Exit Codes

- `0` success
- `1` runtime/validation/conformance failure
- `2` argument or IO usage error

## Testing

```bash
python -m pytest -q eventflow-cli/tests -rs
```

## Notes

- Grouped `validate` is canonical; legacy `validate-*` aliases are intentionally removed.
- Run from repo root for path-bootstrap behavior in tests and local launcher use.
