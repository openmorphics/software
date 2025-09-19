# Wake Word Example

This example demonstrates building a golden trace using audio band events.

Contents
- EIR: examples/wakeword/eir.json
- Input (JSONL): examples/wakeword/traces/inputs/audio_sample.jsonl

Quick start
- python
  ef build --eir examples/wakeword/eir.json --backend cpu-sim --plan-out out/wakeword.plan.json
  ef run --eir examples/wakeword/eir.json \
         --backend cpu-sim \
         --input examples/wakeword/traces/inputs/audio_sample.jsonl \
         --trace-out out/wakeword.golden.jsonl \
         --plan out/wakeword.plan.json
  ef --json compare-traces --golden out/wakeword.golden.jsonl \
                           --candidate out/wakeword.golden.jsonl

Using SAL to generate bands from a WAV (optional)
- python
  ef --json sal-stream \
     --uri "audio.mic://file?path=examples/wakeword/audio.wav&window_ms=20&hop_ms=10&bands=32" \
     --out out/audio_bands.jsonl --telemetry-out out/audio_bands.telemetry.json
  ef run --eir examples/wakeword/eir.json \
         --backend cpu-sim \
         --input out/audio_bands.jsonl \
         --trace-out out/wakeword.golden.jsonl
