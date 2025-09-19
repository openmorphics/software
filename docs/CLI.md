# EventFlow CLI — Specification v0.1

This document describes the EventFlow CLI entrypoints provided by the scaffold in [`python.main()`](eventflow-cli/ef.py:476).

Commands (v0.1)
- list-backends: enumerate available backends (from eventflow-backends)
- build: validate EIR, plan execution (simulator by default)
- run: execute plan with inputs, capture traces and telemetry
- profile: summarize an Event Tensor JSONL or trace (counts, duration, EPS, value stats, dt stats, top channels)
- trace-stats: alias of profile
- compare-traces: conformance check between golden and candidate traces
- validate-eir|validate-event|validate-trace|validate-dcd|validate-efpkg: schema and semantic validators
- package: assemble an EFPKG manifest (see [docs/specs/efpkg.schema.md](docs/specs/efpkg.schema.md))
- sal-stream: normalize a SAL URI (e.g., vision.dvs, audio.mic) into Event Tensor JSONL; supports --telemetry-out and --json for machine-readable telemetry
- Global flag: --json to emit machine-readable output where supported (validators, compare-traces, profile, sal-stream)

Notes
- Backends are discovered via [`python.list_backends()`](eventflow-cli/ef.py:131) which proxies to the registry at [`python.list_backends()`](eventflow-backends/registry/registry.py:77).
- Planning and running routes through the backend registry via [`python.cmd_build()`](eventflow-cli/ef.py:394) and [`python.cmd_run()`](eventflow-cli/ef.py:425).
- Deterministic comparison utilities are implemented in [`python.compare_traces_jsonl()`](eventflow-core/conformance/comparator.py:60).

Examples

List available backends (now includes cpu-sim and gpu-sim):
- python
  ef list-backends

Validate artifacts:
- python
  ef validate-eir --path examples/wakeword/eir.json
  ef validate-event --path examples/wakeword/traces/inputs/audio_sample.jsonl --format auto
  ef validate-dcd --path eventflow-backends/cpu_sim/dcd.json

Build a plan for cpu-sim:
- python
  ef build --eir examples/wakeword/eir.json --backend cpu-sim --plan-out out/wakeword.plan.json

Run and emit a golden trace (inputs already normalized JSONL):
- python
  ef run --eir examples/wakeword/eir.json \
         --backend cpu-sim \
         --input examples/wakeword/traces/inputs/audio_sample.jsonl \
         --trace-out out/wakeword.golden.jsonl \
         --plan out/wakeword.plan.json

Profile an Event Tensor JSONL (with JSON output):
- python
  ef --json profile --path examples/wakeword/traces/inputs/audio_sample.jsonl

SAL + Run workflows (normalize → run → golden → compare)

1) Vision (DVS JSONL → normalize → run)
- python
  ef --json sal-stream \
     --uri "vision.dvs://file?format=jsonl&path=examples/vision_optical_flow/traces/inputs/vision_sample.jsonl" \
     --out out/vision.norm.jsonl --telemetry-out out/vision.telemetry.json
  ef run --eir examples/vision_optical_flow/eir.json \
         --backend cpu-sim \
         --input out/vision.norm.jsonl \
         --trace-out out/vision.golden.jsonl
  ef --json compare-traces --golden out/vision.golden.jsonl \
                           --candidate out/vision.golden.jsonl \
                           --eps-time-us 50 --eps-numeric 1e-5

2) Audio (WAV → bands JSONL → run). If a WAV is not available, use the existing sample JSONL.
- python
  ef --json sal-stream \
     --uri "audio.mic://file?path=examples/wakeword/audio.wav&window_ms=20&hop_ms=10&bands=32" \
     --out out/audio_bands.jsonl --telemetry-out out/audio_bands.telemetry.json
  # or skip SAL and use the provided sample:
  # ef run --eir examples/wakeword/eir.json --backend cpu-sim \
  #        --input examples/wakeword/traces/inputs/audio_sample.jsonl \
  #        --trace-out out/wakeword.golden.jsonl

3) IMU (CSV → JSONL → run) — requires imu.6dof SAL (now supported)
- python
  ef --json sal-stream \
     --uri "imu.6dof://file?path=examples/robotics_slam/traces/inputs/imu_sample.csv" \
     --out out/imu.norm.jsonl --telemetry-out out/imu.telemetry.json
  ef run --eir examples/anomaly_timeseries/eir.json \
         --backend cpu-sim \
         --input out/imu.norm.jsonl \
         --trace-out out/imu.golden.jsonl

Compare traces (golden vs candidate) with JSON output:
- python
  ef --json compare-traces --golden out/wakeword.golden.jsonl \
                           --candidate out/wakeword.golden.jsonl \
                           --eps-time-us 100 --eps-numeric 1e-5

Package an EFPKG manifest:
- python
  ef package --eir examples/wakeword/eir.json \
             --golden out/wakeword.golden.jsonl \
             --input examples/wakeword/traces/inputs/audio_sample.jsonl \
             --model-id wakeword.v1 \
             --model-name "Wakeword v1" \
             --out out/wakeword.efpkg.json

Outputs and run directory layout will follow [docs/CONFORMANCE.md](docs/CONFORMANCE.md).
