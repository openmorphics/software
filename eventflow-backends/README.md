# EventFlow Backends

`eventflow-backends` provides the backend API, backend registry, and simulator implementations. The dependable development target is `cpu-sim`.

## Current State

- Working today: backend discovery, planning, CPU simulator execution, packaged backend metadata, and tests around registry/error behavior.
- Present but limited: GPU/RISC-V-style simulator paths and vendor-backend-shaped modules. Treat these as compatibility/emulation surfaces, not verified hardware support.
- Stubbed or emulated: Loihi, SpiNNaker, and SynSense modules in this community package are not real hardware execution paths.
- Unsupported ops and profiles are reported through explicit planning/runtime errors or emulation metadata.

## Local Usage

From the repository root after editable installation:

```bash
python eventflow-cli/ef.py --json list-backends

python eventflow-cli/ef.py --json run \
  --eir examples/wakeword/eir.json \
  --backend cpu-sim \
  --input examples/wakeword/traces/inputs/audio_sample.jsonl \
  --trace-out out/wakeword.trace.jsonl
```

## Backend Contract

Backends implement the API in `eventflow_backends.api`:

- `compile(...)`: convert EIR/configuration into a backend plan.
- `run_graph(...)`: execute a graph against input events and produce trace output.

The registry should preserve deterministic behavior and make fallback/emulation explicit. Do not silently claim hardware acceleration.

## Testing

```bash
python -m pytest -q eventflow-backends/tests -rs
python -m pytest -q tests/unit/test_planners.py -rs
```
