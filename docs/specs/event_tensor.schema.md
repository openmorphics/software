# EventFlow Event Tensor — JSON Schema and Examples v0.1

Status: Normative schema draft for Event Tensor. Primary carriage format is JSONL (header + records).

Motivation
- Sparse, asynchronous event streams with strict time semantics
- Unit-checked operations and deterministic ordering
- Efficient serialization for interprocess transport

Scope
- Defines the JSON Schema for Event Tensor
- Specifies ordering, units, tolerances, and serialization rules
- Provides examples for DVS, audio, and IMU

JSON Schema (copy-paste as JSON; Draft 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EventFlow Event Tensor",
  "type": "object",
  "required": ["header", "records"],
  "properties": {
    "header": {
      "type": "object",
      "required": ["schema_version", "dims", "units", "dtype", "layout"],
      "additionalProperties": false,
      "properties": {
        "schema_version": { "type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+(-[A-Za-z0-9\\.-]+)?$" },
        "dims": {
          "type": "array",
          "minItems": 1,
          "items": { "type": "string", "minLength": 1 }
        },
        "units": {
          "type": "object",
          "required": ["time", "value"],
          "additionalProperties": false,
          "properties": {
            "time": { "enum": ["ns", "us", "ms"] },
            "value": { "type": "string" }
          }
        },
        "dtype": { "enum": ["f32", "f16", "i16", "u8"] },
        "layout": { "enum": ["coo", "block"] },
        "metadata": { "type": "object" },
        "origin": { "type": "object", "description": "Optional provenance: device id, session id, capture software" }
      }
    },
    "records": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["ts", "idx", "val"],
        "additionalProperties": false,
        "properties": {
          "ts": { "type": "integer", "minimum": 0, "description": "Timestamp in header.units.time" },
          "idx": {
            "type": "array",
            "minItems": 1,
            "items": { "type": "integer", "minimum": 0 }
          },
          "val": { "type": "number" },
          "meta": { "type": "object", "description": "Per-record optional metadata" }
        }
      }
    }
  }
}
```

Notes
- idx length SHOULD match header.dims length; dynamic check performed by validator implementations.
- Time unit is global per tensor; mixing units across tensors requires explicit conversion.
- layout=block indicates batched blocks (future extension); v0.1 readers MAY treat as coo.
- Records MUST be sorted by ts ascending for deterministic replay.

Deterministic ordering
- Primary key: ts
- Secondary key: channel or first spatial index in idx
- Tertiary key: remaining idx lexicographic
- Quaternary key: ingestion order (stable sort)

Overflow and rate limiting (metadata policy)
- Producers SHOULD include rate caps in header.metadata, e.g., {"rate_keps": 500}
- Overflow policy is defined at EIR/runtime but may also be echoed here for audit.

JSONL carriage
- Line 1 MUST be a header object with "header" only.
- Subsequent lines MUST be event records (no wrapping object).

Example — DVS camera (346x260)
```json
{"header":{"schema_version":"0.1.0","dims":["x","y","polarity"],"units":{"time":"us","value":"dimensionless"},"dtype":"u8","layout":"coo","metadata":{"sensor":"dvs","width":346,"height":260}}}
{"ts":100,"idx":[12,45,1],"val":1}
{"ts":104,"idx":[12,45,0],"val":1}
{"ts":133,"idx":[13,45,1],"val":1}
```

Example — Audio bands (STFT encoder)
```json
{"header":{"schema_version":"0.1.0","dims":["band"],"units":{"time":"ms","value":"dB"},"dtype":"f16","layout":"coo","metadata":{"sample_rate":16000,"window_ms":20}}}
{"ts":0,"idx":[3],"val":-24.5}
{"ts":20,"idx":[12],"val":-31.0}
{"ts":40,"idx":[12],"val":-28.0}
```

Example — IMU 6DoF (acceleration)
```json
{"header":{"schema_version":"0.1.0","dims":["axis"],"units":{"time":"us","value":"m_s2"},"dtype":"f32","layout":"coo","metadata":{"axes":["ax","ay","az"]}}}
{"ts":1000,"idx":[0],"val":-0.12}
{"ts":1050,"idx":[1],"val":0.03}
{"ts":1100,"idx":[2],"val":9.81}
```

Validation guidance
- Validate JSON against the schema above.
- Additionally enforce idx length equals dims length and monotonic ts ordering.
- Enforce numeric ranges if domain constraints are known (e.g., polarity in {0,1}).

Interoperability
- For CBOR/MessagePack transport, retain identical field names and units.
- Readers MUST tolerate unknown header.metadata keys.

Change log
- 0.1.0: Initial draft.

Conformance tests (to be added)
- Round-trip validation for example tensors.
- Sorting and tie-break determinism tests.
- Backpressure and overflow logging in end-to-end pipelines.