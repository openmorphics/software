# EventFlow CLI

`eventflow-cli` is the canonical command package for repository workflows. The command behavior lives in `eventflow_cli/main.py`; `ef.py` is only a thin repo-local launcher.

## Current State

- Working today: validation, backend discovery, SAL stream normalization, build/run workflows, trace stats/profile helpers, trace comparison, package commands, and hub subcommands.
- Reliable local usage requires editable installation of the package graph, including `eventflow-license`.
- The CLI intentionally keeps lazy imports for heavier dependencies. Preserve that pattern when adding commands.
- The repo-local launcher should be run from the repository root so path bootstrapping and example paths behave the same way as tests.

## Local Setup

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install \
  -e ./eventflow-core \
  -e ./eventflow-sal \
  -e ./eventflow-backends \
  -e ./eventflow-cli \
  -e ./eventflow-modules \
  -e ./eventflow-hub \
  -e ./eventflow-license
```

Then run:

```bash
python eventflow-cli/ef.py --help
python eventflow-cli/ef.py --json list-backends
```

If installed as a package entrypoint, the command is also available as `eventflow`.

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

## JSON and Exit-Code Contract

- `--json` must emit machine-readable JSON only; do not print extra human text in JSON mode.
- Exit code `0`: success.
- Exit code `1`: validation, conformance, or runtime failure.
- Exit code `2`: argument, usage, or IO error.

## Examples

```bash
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

## Testing

```bash
python -m pytest -q eventflow-cli/tests -rs
```

Grouped `validate` is canonical. Legacy `validate-*` aliases are intentionally removed.
