# EventFlow SAL

Sensor Abstraction Layer (SAL) for EventFlow. SAL normalizes heterogeneous, event-based sensor sources (DVS, audio, IMU, etc.) into deterministic Event Tensor JSONL streams with unit-checked headers, canonical ordering, and timing telemetry.

Features
- URI-based source discovery and configuration (vision.dvs, audio.mic, imu.6dof)
- Deterministic JSONL normalization with header + records
- Timestamp handling with drift/jitter estimation, dt percentiles (p50/p95/p99), and jitter summary (jitter_p50_us/p95/p99)
- Compatibility shim for existing Event Tensor JSONL (pass-through normalization)
- Telemetry JSON output for reproducible pipelines

Quick Start
- python
  ef --json sal-stream \
    --uri "vision.dvs://file?format=jsonl&path=examples/vision_optical_flow/traces/inputs/vision_sample.jsonl" \
    --out out/vision.norm.jsonl --telemetry-out out/vision.telemetry.json

- python
  ef --json sal-stream \
    --uri "audio.mic://file?path=examples/wakeword/audio.wav&window_ms=20&hop_ms=10&bands=32" \
    --out out/audio_bands.jsonl --telemetry-out out/audio_bands.telemetry.json

API
- [api.py](eventflow-sal/api.py) exposes stream_to_jsonl(uri, out, **opts) → telemetry dict
- Drivers and registry:
  - [registry.py](eventflow-sal/eventflow_sal/registry.py)
  - [drivers/dvs.py](eventflow-sal/eventflow_sal/drivers/dvs.py)
  - [drivers/audio.py](eventflow-sal/eventflow_sal/drivers/audio.py)
  - [drivers/imu.py](eventflow-sal/eventflow_sal/drivers/imu.py)
- Data structures:
  - [api/packet.py](eventflow-sal/eventflow_sal/api/packet.py)
  - [api/uri.py](eventflow-sal/eventflow_sal/api/uri.py)

Event Tensor JSONL
- Header (first line): {"header": { schema_version, dims, units, dtype, layout, metadata }}
- Event record lines: {"ts": <us>, "idx": [...], "val": <float|int>}

Notes
- For existing Event Tensor JSONL, use vision.dvs://file?format=jsonl&path=... to enable pass-through normalization (adds telemetry and ensures header).
- Opening JSONL directly via SAL open() is intentionally unsupported; normalization must go through stream_to_jsonl for deterministic behavior.
