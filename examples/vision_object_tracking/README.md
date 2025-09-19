# Vision Object Tracking Example

- EIR: examples/vision_object_tracking/eir.json
- Input DVS JSONL (normalize via SAL if needed)

Commands
- python
  ef run --eir examples/vision_object_tracking/eir.json --backend cpu-sim \
         --input examples/vision_optical_flow/traces/inputs/vision_sample.jsonl \
         --trace-out out/vision_object_tracking.golden.jsonl
