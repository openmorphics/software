# EventFlow CLI

Build, run, profile, normalize streams, and validate EventFlow artifacts.

Commands (selected)
- list-backends — discover available backends
- sal-stream — normalize a SAL URI (vision.dvs, audio.mic, imu.6dof) into Event Tensor JSONL; supports --telemetry-out
- build — plan execution for a backend (JSON plan)
- run — execute a plan (or plan-on-the-fly) and emit a golden trace
- profile (trace-stats) — compute statistics for Event Tensor JSONL
- compare-traces — conformance (golden vs candidate)
- validate-* — schema and semantic validators
- package — emit EFPKG manifest (EIR, traces, inputs, hashes, metadata)

JSON output mode
- Add --json to emit machine-readable JSON where supported (sal-stream, compare-traces, version, list-backends, package, validators).

Examples
- python
  ef --json sal-stream \
    --uri "vision.dvs://file?format=jsonl&path=examples/vision_optical_flow/traces/inputs/vision_sample.jsonl" \
    --out out/vision.norm.jsonl --telemetry-out out/vision.telemetry.json

- python
  ef --json compare-traces \
    --golden examples/vision_optical_flow/traces/golden/vision.golden.jsonl \
    --candidate out/vision.norm.jsonl \
    --eps-time-us 50 --eps-numeric 1e-5
