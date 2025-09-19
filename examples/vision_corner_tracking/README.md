# Vision Corner Tracking Example

- EIR: examples/vision_corner_tracking/eir.json
- Input DVS JSONL (create via generator or use existing samples)

Generate a tiny synthetic DVS stream:
- bash
  tools/gen_dvs_synthetic.py --path examples/vision_corner_tracking/traces/inputs/corner_sample.jsonl

Normalize (optional) and run:
- python
  ef --json sal-stream --uri "vision.dvs://file?format=jsonl&path=examples/vision_corner_tracking/traces/inputs/corner_sample.jsonl" \
     --out out/corner.norm.jsonl --telemetry-out out/corner.telemetry.json
  ef run --eir examples/vision_corner_tracking/eir.json --backend cpu-sim \
         --input out/corner.norm.jsonl --trace-out out/corner.golden.jsonl
