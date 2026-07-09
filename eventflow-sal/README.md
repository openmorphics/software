# EventFlow SAL

`eventflow-sal` is the Sensor Abstraction Layer. Its useful job today is normalizing supported file/replay sources into deterministic Event Tensor JSONL streams with headers, canonical ordering, and timing telemetry.

## Current State

- Working today: JSONL pass-through normalization, WAV/audio band extraction paths, CSV-style IMU replay paths, URI parsing, packet structures, telemetry, and deterministic stream output.
- Partially implemented: several domain-specific replay drivers exist as simple synthetic/file adapters.
- Stubbed: live device sources for DVS, microphone, IMU, tactile, bio, industrial, environmental, security, and similar domains mostly yield no events unless a file/replay path is implemented.
- Intentional contract: opening JSONL directly through `open()` is unsupported; deterministic normalization should go through `stream_to_jsonl()`.

## Quick Start

From the repository root after editable installation:

```bash
python eventflow-cli/ef.py --json sal-stream \
  --uri "vision.dvs://file?format=jsonl&path=examples/vision_optical_flow/traces/inputs/vision_sample.jsonl" \
  --out out/vision.norm.jsonl \
  --telemetry-out out/vision.telemetry.json

python eventflow-cli/ef.py --json sal-stream \
  --uri "audio.mic://file?path=examples/wakeword/audio.wav&window_ms=20&hop_ms=10&bands=32" \
  --out out/audio_bands.jsonl \
  --telemetry-out out/audio_bands.telemetry.json
```

## API

- `eventflow_sal.stream.stream_to_jsonl(uri, out, **opts)`: normalize a source URI to Event Tensor JSONL and return telemetry.
- `eventflow_sal.registry`: resolve supported URI schemes into source implementations.
- `eventflow_sal.api.packet`: Event Tensor packet/header data structures.
- `eventflow_sal.api.uri`: URI parsing helpers.

## Event Tensor JSONL

The first line is a header:

```json
{"header": {"schema_version": "...", "dims": [], "units": {}, "dtype": "...", "layout": "...", "metadata": {}}}
```

Subsequent lines are event records:

```json
{"ts": 0, "idx": [0], "val": 1.0}
```

## Testing

```bash
python -m pytest -q eventflow-sal/tests -rs
python -m pytest -q tests/unit/test_sal_driver_smoke.py tests/unit/test_sal_registry_dispatch.py -rs
```
