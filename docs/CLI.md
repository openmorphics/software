# EventFlow CLI Reference

Canonical CLI implementation lives in `eventflow-cli/eventflow_cli/main.py`.
Repo-local launcher `eventflow-cli/ef.py` is intentionally thin and delegates to that canonical main.

## Invocation

From repo root:

```bash
python eventflow-cli/ef.py --help
```

Installed entrypoint (optional):

```bash
eventflow --help
```

## Global Option

- `--json`: emit machine-readable JSON where supported.

## Commands

- `version`: print SDK version
- `list-backends`: discover available backends
- `validate`: grouped validator entrypoint
- `sal-stream`: normalize SAL URI source to Event Tensor JSONL
- `profile`: profile Event Tensor JSONL file
- `trace-stats`: alias of `profile`
- `package`: create EFPKG manifest
- `build`: validate EIR and produce backend plan
- `run`: execute backend run and emit trace
- `compare-traces`: compare golden/candidate traces
- `hub`: local package registry operations

## Validate (Grouped)

Exactly one target is required:

- `--eir`
- `--event`
- `--trace`
- `--dcd`
- `--efpkg`

Example:

```bash
python eventflow-cli/ef.py --json validate --eir examples/vision_optical_flow/eir.json
python eventflow-cli/ef.py --json validate --event examples/wakeword/traces/inputs/audio_sample.jsonl
python eventflow-cli/ef.py --json validate --trace examples/wakeword/traces/golden/wakeword.golden.jsonl
python eventflow-cli/ef.py --json validate --dcd eventflow-backends/eventflow_backends/cpu_sim/dcd.json
```

## SAL Stream

Supported v0.1 URIs commonly used in tests/examples:

- `vision.dvs://file?format=jsonl&path=...`
- `audio.mic://file?path=...`
- `imu.6dof://file?path=...`

Example:

```bash
python eventflow-cli/ef.py --json sal-stream \
  --uri "vision.dvs://file?format=jsonl&path=examples/vision_optical_flow/traces/inputs/vision_sample.jsonl" \
  --out out/vision.norm.jsonl \
  --telemetry-out out/vision.telemetry.json
```

## Build and Run

```bash
python eventflow-cli/ef.py --json build \
  --eir examples/vision_optical_flow/eir.json \
  --backend cpu-sim \
  --plan-out out/vision.plan.json

python eventflow-cli/ef.py --json run \
  --eir examples/vision_optical_flow/eir.json \
  --backend cpu-sim \
  --input out/vision.norm.jsonl \
  --trace-out out/vision.trace.jsonl \
  --plan out/vision.plan.json
```

## Compare Traces

```bash
python eventflow-cli/ef.py --json compare-traces \
  --golden examples/vision_optical_flow/traces/golden/vision.golden.jsonl \
  --candidate out/vision.trace.jsonl \
  --eps-time-us 100 \
  --eps-numeric 1e-5
```

## Profile / Trace Stats

```bash
python eventflow-cli/ef.py --json profile --path out/vision.trace.jsonl
python eventflow-cli/ef.py --json trace-stats --path out/vision.trace.jsonl
```

## Package

```bash
python eventflow-cli/ef.py --json package \
  --eir examples/wakeword/eir.json \
  --golden examples/wakeword/traces/golden/wakeword.golden.jsonl \
  --input examples/wakeword/traces/inputs/audio_sample.jsonl \
  --model-id wakeword.v1 \
  --model-name "Wakeword v1" \
  --out out/wakeword.efpkg.json
```

## Hub

```bash
python eventflow-cli/ef.py hub --help
python eventflow-cli/ef.py hub list
```

## Exit Code Contract

- `0`: success
- `1`: validation/conformance/runtime failure
- `2`: argument or file/IO style usage error

## Notes

- Legacy `validate-eir` / `validate-event` / `validate-dcd` / `validate-efpkg` / `validate-trace` aliases are intentionally removed.
- For test parity, repo-local invocation should be used from repo root.
