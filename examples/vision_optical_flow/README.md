# Vision Optical Flow + Gesture Example

This example normalizes DVS events with SAL and emits a golden trace.

- Input DVS sample: examples/vision_optical_flow/traces/inputs/vision_sample.jsonl
- EIR: examples/vision_optical_flow/eir.json

Commands
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
