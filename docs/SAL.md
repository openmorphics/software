# Sensor Abstraction Layer (SAL) — Specification v0.1

Status: Normative specification for EventFlow SAL. SAL normalizes heterogeneous event-based sensors into Event Tensors and enforces timing, safety, and integrity constraints.

Related specifications
- Event Tensor schema: [docs/specs/event_tensor.schema.md](docs/specs/event_tensor.schema.md)
- EIR IR schema: [docs/specs/eir.schema.md](docs/specs/eir.schema.md)
- Device Capability Descriptor (DCD): [docs/specs/dcd.schema.md](docs/specs/dcd.schema.md)
- Packaging (EFPKG): [docs/specs/efpkg.schema.md](docs/specs/efpkg.schema.md)
- Architecture overview: [docs/SPEC.md](docs/SPEC.md)

Goals
- Provide hardware-agnostic, sensor-agnostic ingestion for event-driven applications.
- Convert vendor/device formats into deterministic, unit-checked Event Tensors.
- Synchronize device clocks, mitigate drift/jitter, and enforce ordering guarantees.
- Enforce rate limiting and overflow protections; detect spoofing/anomalies.
- Offer a uniform URI-based open() interface and driver registry.

Scope
- Standard source types, Event Tensor mappings, time model, synchronization algorithms.
- Drivers for DVS playback (AEDAT) and live microphone band events (STFT) in v0.1; IMU/tactile/bio stubs.
- Safety, rate, and overflow policies; telemetry counters; conformance tests.

---

## 1. Source types and Event Tensor mapping

SAL defines canonical source types and their mapping to Event Tensor headers/records. See [docs/specs/event_tensor.schema.md](docs/specs/event_tensor.schema.md) for schema.

1.1. vision.dvs (Dynamic Vision Sensor)
- dims: ["x","y","polarity"]
- units: time: us; value: "dimensionless"
- dtype: u8; val ∈ {0,1}
- metadata: sensor="dvs", width, height, vendor, model, biases
- Records: {"ts": T, "idx":[x,y,p], "val":1}

1.2. audio.mic (Microphone, band events via streaming STFT)
- dims: ["band"] or ["channel","band"] for multi-channel
- units: time: ms or us; value: "dB" (or "power" if linear)
- dtype: f16|f32
- metadata: sample_rate, window_ms, hop_ms, window_fn
- Records: {"ts": T, "idx":[band], "val": dB}

1.3. imu.6dof (Accelerometer + Gyro)
- dims: ["axis"] (e.g., 0=ax,1=ay,2=az,3=gx,4=gy,5=gz) or split streams
- units: time: us; value: "m_s2" or "rad_s"
- dtype: f32
- metadata: axes, scale_factors, calibration_ts

1.4. tactile.array
- dims: ["taxel"]
- units: time: us; value: "pascal" (or "dimensionless" if normalized)
- dtype: f16|f32

1.5. bio.ppg / bio.ecg
- dims: ["channel"]
- units: time: ms|us; value per modality
- dtype: f16|f32
- Note: threshold/feature-crossing events may encode val as 1 with channel=feature_id.

Producers MUST ensure that idx length equals dims length and that ts is monotonically non-decreasing after SAL synchronization. See Deterministic ordering (Section 3.4).

---

## 2. SAL driver interface and URIs

2.1. Open and configuration
- SAL.open(uri: str, **kwargs) → source handle
- SAL.read(source, n: int|duration) → iterator or batches of Event Tensor JSONL frames
- SAL.close(source)

2.2. URIs (examples)
- "vision.dvs://file?format=aedat4&path=/data/seq.aedat4"
- "audio.mic://default?rate=16000&window_ms=20&hop_ms=10"
- "imu.6dof://device0?rate=1000"

2.3. Registry and discovery
- Drivers register a scheme prefix (e.g., "vision.dvs", "audio.mic") and supported query params.
- Unknown schemes MUST raise a standardized "sal.unsupported_source" error.

2.4. Backpressure and buffering
- SAL MUST expose an internal bounded buffer per source. If full, behavior follows EIR/security overflow_policy (drop_head, drop_tail, or block). See [docs/specs/eir.schema.md](docs/specs/eir.schema.md).

---

## 3. Time model, synchronization, and ordering

3.1. Timestamp domains
- Device clock T_dev and host monotonic clock T_host. SAL maintains a mapping T_host ≈ α·T_dev + β.
- For recorded files (e.g., AEDAT), the file's timestamps become T_dev; SAL normalizes to T_out per configuration.

3.2. Synchronization strategies
- host_sync (default): Estimate affine transform via rolling linear regression on (T_dev, T_host) pairs from periodic device heartbeats.
- ntp/ptp: If device supports NTP/PTP, SAL may treat T_dev ≈ T_host, still bounding drift via jitter estimates.
- fixed_step alignment (optional): For fixed-step execution pipelines, SAL quantizes to dt and tracks quantization error (see Determinism).

3.3. Drift and jitter estimation
- Maintain exponential moving averages for observed drift (ppm) and jitter (ns).
- Expose SAL.sync_status(): { drift_ppm, jitter_ns, last_sync_ts }.

3.4. Deterministic ordering
- Sort events by ts ascending; tie-break by idx[0] (channel or primary spatial axis), then remaining idx lexicographically, then ingestion order (stable).
- SAL MUST NOT output events out-of-order after synchronization; partial reorder buffers must be large enough to absorb expected jitter.

3.5. Units
- SAL enforces declared units in Event Tensor headers. Conversion from device-native units MUST be explicit and configurable.

---

## 4. Rate limiting, overflow policies, and safety

4.1. Rate limits
- Per-channel cap expressed as kilo-events-per-second (keps). Configurable via:
  - Graph-level defaults in EIR.security (see [docs/specs/eir.schema.md](docs/specs/eir.schema.md)).
  - Source-level overrides in SAL.open(..., rate_limit_keps=...).
- SAL MUST maintain counters: produced, dropped_head, dropped_tail, blocked_time_ms.

4.2. Overflow policies
- drop_head: drop oldest buffered events
- drop_tail: drop newest incoming events
- block: backpressure (may increase latency; REALTIME profile may forbid)
- Default selection from EIR.security.overflow_policy; SAL-level overrides allowed.

4.3. Safety guards
- Value range checks (e.g., polarity∈{0,1} for DVS)
- Index bounds (x∈[0,width), y∈[0,height))
- Reject NaN/Inf payloads when dtype is finite
- Optional clipping or normalization

---

## 5. Spoofing and anomaly detection (baseline)

5.1. Inter-event interval (IEI) anomalies
- Maintain histograms of IEIs per channel; flag bursts with improbably low IEIs beyond configured sigma thresholds.

5.2. Spatial correlations (vision.dvs)
- Detect excessively wide simultaneous activations (e.g., >X% pixels toggled in Δt) as potential flashes/spoof.

5.3. Audio band anomalies
- Flag narrowband spikes exceeding dynamic threshold relative to rolling median and MAD.

5.4. Policy
- On detection, emit SAL telemetry events and optionally attenuate or drop affected records. Policy is configurable.

---

## 6. v0.1 reference drivers

6.1. DVS playback (AEDAT)
- Input: AEDAT 3/4 files or streams
- Output: Event Tensor JSONL with dims ["x","y","polarity"], units.time="us"
- Config:
  - normalize_ts: "host"|"file" (default "file")
  - width, height (if not in file metadata)
  - polarity_map: { "on":1, "off":0 } (default)
  - rate_limit_keps (optional)
  - overflow_policy (optional)
- File carriage: first JSON line is header; subsequent lines are records (see [docs/specs/event_tensor.schema.md](docs/specs/event_tensor.schema.md)).

6.2. Microphone live capture (audio.mic)
- Input: host audio device (default) or named device
- Output: band events (STFT)
- Config:
  - sample_rate (e.g., 16000)
  - window_ms (e.g., 20), hop_ms (e.g., 10)
  - window_fn (hann|hamming|rect)
  - channels: 1|2|… ; dims ["band"] or ["channel","band"]
  - units.value: "dB" or "power"
  - dtype: f16|f32
  - rate_limit_keps and overflow_policy optional

6.3. IMU 6DoF (stub)
- Input: host IMU/joint sensor source
- Output: acceleration/gyro events
- Config: rate, axes mapping, calibration constants
- Units: m_s2 and rad_s

---

## 7. Configuration and policy precedence

Order of precedence (highest to lowest):
1) SAL.open(...) explicit kwargs
2) EIR graph-level security defaults (see [docs/specs/eir.schema.md](docs/specs/eir.schema.md))
3) SAL driver defaults

SAL MUST surface the effective configuration via source.get_effective_config() for audit.

---

## 8. Telemetry and counters

SAL MUST emit:
- per-source counters: produced, dropped_head, dropped_tail, blocked_time_ms, reordered, anomalies_detected
- sync status: drift_ppm, jitter_ns, last_sync_ts
- rates: events_per_sec (EMA), per-channel where applicable

For JSONL telemetry schema, see profiling notes in [docs/SPEC.md](docs/SPEC.md).

---

## 9. Conformance tests (SAL)

To pass SAL conformance:
- Deterministic ordering: Given fixed recorded inputs, output ordering and timestamps are stable across runs.
- Unit invariants: Header units consistent; conversions correct within tolerance.
- Rate/overflow: Induce overflow and verify policy behavior with counters.
- Spoof detection: Inject adversarial patterns and verify anomaly flags.
- Sync: Simulate drift; verify SAL recovers and bounds jitter.

---

## 10. Errors and diagnostics

Standard SAL error codes (string identifiers):
- "sal.unsupported_source": unknown URI scheme
- "sal.open_failed": device/file cannot be opened
- "sal.decode_error": vendor format parsing failed
- "sal.sync_unstable": synchronization cannot satisfy required jitter bounds
- "sal.overflow": buffer overrun beyond configured policy
- "sal.security_violation": out-of-range or malformed records

Drivers MUST provide actionable messages and include suggested remediation steps.

---

## 11. Versioning and compatibility

- SAL interfaces are versioned with the SDK; minor versions may add optional fields and drivers.
- Driver-specific metadata keys MUST NOT collide with reserved keys in Event Tensor header.
- Backward compatibility: older clients MUST be able to ignore unknown metadata keys.

Change log
- 0.1.0: Initial SAL specification and reference driver definitions (DVS playback, audio mic STFT).