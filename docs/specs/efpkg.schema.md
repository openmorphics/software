# EventFlow Packaging (EFPKG) — Manifest JSON Schema and Bundle Layout v0.1

Status: Normative schema draft for portable EventFlow artifacts (models, graphs, traces, and compatibility metadata).

Purpose
- Enable reproducible deployment across environments and backends with deterministic semantics.
- Bundle all required artifacts: EIR, capability requirements, golden traces, profiles, and metadata.
- Support integrity (hashes), provenance, semantic versioning, and feature flags.

Related specifications
- EIR schema: [`docs/specs/eir.schema.md`](docs/specs/eir.schema.md)
- Event Tensor schema: [`docs/specs/event_tensor.schema.md`](docs/specs/event_tensor.schema.md)
- Device Capability Descriptor (DCD): [`docs/specs/dcd.schema.md`](docs/specs/dcd.schema.md)
- Architecture + packaging overview: [`docs/SPEC.md`](docs/SPEC.md)

Scope
- Defines the EFPKG bundle structure.
- Provides the Manifest JSON Schema (applies to either YAML or JSON manifest).
- Includes examples and validation rules.

---

## 1. Bundle structure

An EFPKG is a directory (or a single-file archive like .zip/.tar.zst with the same internal structure) containing:

```
efpkg/
├── manifest.yaml                  # Required manifest (YAML or JSON)
├── eir.json                       # EIR graph (JSON) referencing [`docs/specs/eir.schema.md`](docs/specs/eir.schema.md)
├── capabilities.required.json     # Capability requirements subset of DCD; see [`docs/specs/dcd.schema.md`](docs/specs/dcd.schema.md)
├── traces/
│   ├── golden.trace.jsonl         # Golden probe outputs (JSONL), see [`docs/specs/event_tensor.schema.md`](docs/specs/event_tensor.schema.md)
│   └── inputs/                    # Optional input event streams used to generate golden traces
│       ├── vision_sample.jsonl
│       └── audio_sample.jsonl
├── profiles/
│   └── baseline.profile.jsonl     # Optional JSONL telemetry baseline (latency, throughput, drop rates)
├── assets/                        # Optional domain assets (weights, lookup tables)
│   └── readme.md
├── checksums.txt                  # Optional sha256/sha512 sums for all included files
└── signatures.txt                 # Optional provenance / signing info
```

Notes
- `manifest.yaml` may also be `manifest.json`; schema is identical.
- File names under `traces/inputs` and `assets/` are unconstrained; the manifest references them logically.

---

## 2. Manifest JSON Schema (Draft 2020-12)

Copy-paste as JSON; use to validate either YAML or JSON manifests.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EventFlow Package (EFPKG) Manifest",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "sdk_version",
    "model",
    "profile",
    "determinism",
    "artifacts"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+(-[A-Za-z0-9\\.-]+)?$",
      "description": "Version of the EFPKG manifest schema (e.g., 0.1.0)"
    },
    "sdk_version": {
      "type": "string",
      "description": "EventFlow SDK version that produced the package (semver)"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "ISO8601 timestamp of package creation"
    },
    "model": {
      "type": "object",
      "additionalProperties": false,
      "required": ["id", "name"],
      "properties": {
        "id": { "type": "string", "description": "Unique model/package ID (UUID or slug)" },
        "name": { "type": "string" },
        "description": { "type": "string" },
        "version": { "type": "string", "description": "Model semantic version (user-level)" },
        "author": { "type": "string" },
        "license": { "type": "string" },
        "tags": { "type": "array", "items": { "type": "string" } },
        "domains": {
          "type": "array",
          "items": { "enum": ["vision", "audio", "robotics", "timeseries", "wellness", "creative"] }
        }
      }
    },
    "profile": {
      "type": "object",
      "additionalProperties": false,
      "required": ["name"],
      "properties": {
        "name": { "enum": ["BASE", "REALTIME", "LEARNING", "LOWPOWER"] },
        "notes": { "type": "string" },
        "constraints": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "latency_budget_ms": { "type": "number", "minimum": 0 },
            "max_drop_rate_pct": { "type": "number", "minimum": 0, "maximum": 100 }
          }
        }
      }
    },
    "determinism": {
      "type": "object",
      "additionalProperties": false,
      "required": ["time_unit", "mode", "epsilon_time_us", "epsilon_numeric", "seed"],
      "properties": {
        "time_unit": { "enum": ["ns", "us", "ms"] },
        "mode": { "enum": ["exact_event", "fixed_step"] },
        "fixed_step_dt_us": { "type": "integer", "minimum": 1 },
        "epsilon_time_us": { "type": "integer", "minimum": 0 },
        "epsilon_numeric": { "type": "number", "minimum": 0 },
        "seed": { "type": "integer", "minimum": 0 }
      },
      "allOf": [
        {
          "if": { "properties": { "mode": { "const": "fixed_step" } } },
          "then": { "required": ["fixed_step_dt_us"] }
        }
      ]
    },
    "features": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Optional feature flags that the model requires (e.g., 'plasticity', 'conv2d_events')"
    },
    "capabilities_required": {
      "type": "object",
      "description": "Subset compatible with DCD schema; denotes minimal backend capabilities required",
      "additionalProperties": true
    },
    "artifacts": {
      "type": "object",
      "additionalProperties": false,
      "required": ["eir", "traces"],
      "properties": {
        "eir": {
          "type": "object",
          "additionalProperties": false,
          "required": ["path", "format"],
          "properties": {
            "path": { "type": "string", "description": "Relative path to EIR JSON (e.g., 'eir.json')" },
            "format": { "enum": ["json"], "default": "json" },
            "sha256": { "type": "string", "pattern": "^[A-Fa-f0-9]{64}$" },
            "filesize_bytes": { "type": "integer", "minimum": 0 }
          }
        },
        "traces": {
          "type": "object",
          "additionalProperties": false,
          "required": ["golden"],
          "properties": {
            "golden": {
              "type": "object",
              "additionalProperties": false,
              "required": ["path", "format"],
              "properties": {
                "path": { "type": "string", "description": "Probe outputs in JSONL" },
                "format": { "enum": ["jsonl"] },
                "sha256": { "type": "string", "pattern": "^[A-Fa-f0-9]{64}$" }
              }
            },
            "inputs": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": ["path", "format"],
                "properties": {
                  "path": { "type": "string" },
                  "format": { "enum": ["jsonl"] },
                  "sha256": { "type": "string", "pattern": "^[A-Fa-f0-9]{64}$" }
                }
              }
            }
          }
        },
        "profiles": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "baseline": {
              "type": "object",
              "additionalProperties": false,
              "required": ["path", "format"],
              "properties": {
                "path": { "type": "string" },
                "format": { "enum": ["jsonl"] },
                "sha256": { "type": "string", "pattern": "^[A-Fa-f0-9]{64}$" }
              }
            }
          }
        },
        "assets": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["path"],
            "properties": {
              "path": { "type": "string" },
              "sha256": { "type": "string", "pattern": "^[A-Fa-f0-9]{64}$" }
            }
          }
        }
      }
    },
    "integrity": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "checksums": { "type": "string", "description": "Relative path to checksums.txt if present" },
        "signatures": { "type": "string", "description": "Relative path to signatures.txt if present" }
      }
    },
    "compatibility": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "tested_backends": {
          "type": "array",
          "items": {
            "type": "object",
            "additionalProperties": false,
            "required": ["name", "version"],
            "properties": {
              "name": { "type": "string" },
              "version": { "type": "string" },
              "notes": { "type": "string" }
            }
          }
        }
      }
    },
    "notes": { "type": "string" }
  }
}
```

Validation notes
- `capabilities_required` should be validated by the DCD schema where applicable.
- `determinism` SHOULD match the EIR configuration (same mode, dt, epsilons, seed).
- All artifact paths MUST be relative and MUST resolve inside the bundle.
- If `profiles.baseline` is present, its telemetry schema should align with profiling JSONL documented in [`docs/SPEC.md`](docs/SPEC.md).

---

## 3. Example manifest (YAML)

```yaml
schema_version: "0.1.0"
sdk_version: "0.1.0"
created_at: "2025-09-18T18:20:00Z"
model:
  id: "ef.demo.wakeword"
  name: "Wake Word KWS"
  description: "Keyword spotter for 'hey event'"
  version: "0.1.0"
  author: "EventFlow Team"
  license: "Apache-2.0"
  tags: ["audio", "kws", "demo"]
  domains: ["audio"]
profile:
  name: "BASE"
  constraints:
    latency_budget_ms: 10
    max_drop_rate_pct: 1.0
determinism:
  time_unit: "us"
  mode: "fixed_step"
  fixed_step_dt_us: 100
  epsilon_time_us: 100
  epsilon_numeric: 1.0e-5
  seed: 42
features: ["conv1d_events", "probe_spike"]
capabilities_required:
  deterministic_modes: ["fixed_step"]
  supported_ops: ["lif", "synapse_exp", "conv1d_events", "probe_spike"]
  time_resolution_ns: 1000
artifacts:
  eir:
    path: "eir.json"
    format: "json"
    sha256: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    filesize_bytes: 4096
  traces:
    golden:
      path: "traces/golden.trace.jsonl"
      format: "jsonl"
      sha256: "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
    inputs:
      - path: "traces/inputs/audio_sample.jsonl"
        format: "jsonl"
        sha256: "1111111111111111111111111111111111111111111111111111111111111111"
  profiles:
    baseline:
      path: "profiles/baseline.profile.jsonl"
      format: "jsonl"
      sha256: "2222222222222222222222222222222222222222222222222222222222222222"
assets:
  - path: "assets/readme.md"
integrity:
  checksums: "checksums.txt"
compatibility:
  tested_backends:
    - name: "cpu-sim"
      version: "0.1.0"
      notes: "Deterministic by construction"
notes: "Initial demo packaging."
```

---

## 4. Example directory tree

```
efpkg/
├── manifest.yaml
├── eir.json
├── capabilities.required.json
├── traces/
│   ├── golden.trace.jsonl
│   └── inputs/
│       └── audio_sample.jsonl
├── profiles/
│   └── baseline.profile.jsonl
├── assets/
│   └── readme.md
└── checksums.txt
```

---

## 5. Integrity and provenance

- `checksums.txt` SHOULD list `sha256 <hex>  <relative-path>` for every artifact line by line.
- `signatures.txt` MAY include cryptographic signatures (e.g., minisign, cosign) and public key metadata.
- Manifest-specified `sha256` SHOULD match computed values; verifiers MUST fail on mismatch.

---

## 6. Determinism and equivalence

- The runtime MUST honor `determinism` and the EIR’s time configuration. Replays on simulator backends MUST be bit-exact; across backends, golden equivalence MUST hold within `epsilon_time_us` and `epsilon_numeric`.
- If a target cannot satisfy the profile constraints, deployment SHOULD fail with a compatibility error and include remediation suggestions.

---

## 7. Backward/forward compatibility

- `schema_version` follows semver; fields MAY be added in minor versions under `additionalProperties: false` only if guarded by feature flags or optional properties.
- Major-version changes MAY break parsers; tools SHOULD advertise supported schema versions.

---

## 8. Conformance checks

A package passes conformance when:
- Manifest validates against the schema above.
- EIR validates and compiles for at least one supported backend (e.g., cpu-sim).
- Golden trace replay matches within epsilon bounds.
- Optional baseline profile (if present) matches latency thresholds within tolerance.

---

## 9. Change log

- 0.1.0: Initial EFPKG manifest schema and bundle layout.