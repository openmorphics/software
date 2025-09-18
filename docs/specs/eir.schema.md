# EventFlow Event Intermediate Representation (EIR) — JSON Schema and Examples v0.1

Status: Normative schema draft for EventFlow's hardware- and sensor-agnostic IR. This schema is the thin waist for compilation, execution, packaging, and conformance.

Related specifications
- Event Tensor (events I/O): [docs/specs/event_tensor.schema.md](docs/specs/event_tensor.schema.md)
- Device Capability Descriptor (DCD): [docs/specs/dcd.schema.md](docs/specs/dcd.schema.md)
- Packaging (EFPKG): [docs/specs/efpkg.schema.md](docs/specs/efpkg.schema.md)
- Architecture overview: [docs/SPEC.md](docs/SPEC.md)

Design goals
- Deterministic time semantics (exact-event and fixed-step) with unit checks and global seeded RNG.
- Extensible opset for spiking primitives (neurons, synapses, delays), kernels, and domain-specific operators.
- Explicit timing constraints, security policies, and probes for trace capture.
- Strict JSON Schema to enable early validation and reproducible pipelines.

JSON Schema (Draft 2020-12)
Copy-paste as JSON. Use this to validate EIR JSON artifacts (and also YAML after conversion).

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EventFlow EIR",
  "type": "object",
  "additionalProperties": false,
  "required": ["version", "profile", "time", "graph", "nodes", "edges"],
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+(-[A-Za-z0-9\\.-]+)?$",
      "description": "EIR document schema version (semver)"
    },

    "profile": {
      "type": "string",
      "enum": ["BASE", "REALTIME", "LEARNING", "LOWPOWER"]
    },

    "seed": {
      "type": "integer",
      "minimum": 0,
      "description": "Global 64-bit seed for RNG; operators derive per-node streams deterministically"
    },

    "time": {
      "type": "object",
      "additionalProperties": false,
      "required": ["unit", "mode"],
      "properties": {
        "unit": { "type": "string", "enum": ["ns", "us", "ms"] },
        "mode": { "type": "string", "enum": ["exact_event", "fixed_step"] },
        "fixed_step_dt_us": { "type": "integer", "minimum": 1 },
        "epsilon_time_us": { "type": "integer", "minimum": 0, "default": 100 },
        "epsilon_numeric": { "type": "number", "minimum": 0, "default": 1e-5 }
      },
      "allOf": [
        {
          "if": { "properties": { "mode": { "const": "fixed_step" } } },
          "then": { "required": ["fixed_step_dt_us"] }
        }
      ]
    },

    "graph": {
      "type": "object",
      "additionalProperties": false,
      "required": ["name"],
      "properties": {
        "name": { "type": "string", "minLength": 1 },
        "attributes": { "type": "object", "description": "Free-form metadata (e.g., tags, author, domain)" }
      }
    },

    "nodes": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "kind"],
        "properties": {
          "id": { "type": "string", "minLength": 1 },
          "kind": {
            "type": "string",
            "description": "Operator kind",
            "enum": [
              "spiking_neuron",
              "synapse",
              "delay_line",
              "kernel",
              "group",
              "route",
              "probe",
              "custom"
            ]
          },
          "op": {
            "type": "string",
            "description": "Specific operator name (e.g., lif, glif, synapse_exp, conv2d_events); required for kind=spiking_neuron|synapse|kernel"
          },
          "params": {
            "type": "object",
            "description": "Operator parameters (e.g., tau, threshold, kernel size)"
          },
          "state": {
            "type": "object",
            "description": "Optional initial state (e.g., membrane potentials, synaptic traces)"
          },
          "timing_constraints": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "deadline_us": { "type": "integer", "minimum": 0 },
              "refractory_us": { "type": "integer", "minimum": 0 },
              "max_latency_us": { "type": "integer", "minimum": 0 }
            }
          },
          "security": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "sandbox": { "type": "boolean", "default": true },
              "rate_limit_keps": { "type": "integer", "minimum": 0 },
              "overflow_policy": { "type": "string", "enum": ["drop_head", "drop_tail", "block"] }
            }
          }
        },
        "allOf": [
          {
            "if": { "properties": { "kind": { "enum": ["spiking_neuron", "synapse", "kernel"] } } },
            "then": { "required": ["op"] }
          }
        ]
      }
    },

    "edges": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["src", "dst"],
        "properties": {
          "src": { "type": "string" },
          "dst": { "type": "string" },
          "weight": { "type": "number" },
          "delay_us": { "type": "integer", "minimum": 0 },
          "plasticity": {
            "type": "object",
            "additionalProperties": false,
            "properties": {
              "kind": { "type": "string", "enum": ["STDP", "Hebbian", "Custom"] },
              "params": { "type": "object" }
            }
          }
        }
      }
    },

    "probes": {
      "type": "array",
      "description": "Optional probe declarations; a probe may also be modeled as a node kind=probe",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["id", "target"],
        "properties": {
          "id": { "type": "string" },
          "target": { "type": "string", "description": "Node id or pattern" },
          "type": { "type": "string", "enum": ["spike", "rate", "current", "voltage", "custom"], "default": "spike" },
          "window_us": { "type": "integer", "minimum": 0 }
        }
      }
    },

    "security": {
      "type": "object",
      "additionalProperties": false,
      "description": "Graph-level security defaults, may be overridden per-node",
      "properties": {
        "sandbox": { "type": "boolean", "default": true },
        "rate_limit_keps": { "type": "integer", "minimum": 0 },
        "overflow_policy": { "type": "string", "enum": ["drop_head", "drop_tail", "block"] }
      }
    },

    "metadata": {
      "type": "object",
      "description": "Optional provenance and documentation (e.g., author, license, dataset references)"
    }
  }
}
```

Normative constraints
- Nodes and edges MUST form a directed multigraph without cycles unless explicitly permitted by `kind="group"` or `op` semantics that ensure stable dynamics (e.g., delays).
- For `exact_event` mode, execution MUST process events in strictly increasing timestamp order; ties are broken deterministically by (channel or first spatial index), then remaining index lexicographically, then ingestion order.
- For `fixed_step` mode, the system MUST discretize time using `fixed_step_dt_us` and track quantization error; end-to-end jitter MUST remain within `epsilon_time_us`.
- Randomness MUST derive solely from the EIR `seed` using counter-based RNGs to avoid order sensitivity.
- Overflow policy MUST be enforced by runtime per graph/node settings.

Recommended operator identifiers
- Spiking neurons: lif, glif, adex, izhikevich
- Synapses: synapse_exp, synapse_alpha, synapse_delta
- Delay lines: delay_line
- Domain kernels (examples): conv1d_events, conv2d_events, pooling_events, optical_flow_events, corner_detect_events, kws_events

Example 1 — Minimal LIF pair (fixed-step)

```json
{
  "version": "0.1.0",
  "profile": "BASE",
  "seed": 42,
  "time": { "unit": "us", "mode": "fixed_step", "fixed_step_dt_us": 100, "epsilon_time_us": 100, "epsilon_numeric": 1e-5 },
  "graph": { "name": "lif_pair" },
  "nodes": [
    { "id": "pop0", "kind": "spiking_neuron", "op": "lif", "params": { "size": 128, "tau_ms": 10.0, "v_th": 1.0 } },
    { "id": "pop1", "kind": "spiking_neuron", "op": "lif", "params": { "size": 128, "tau_ms": 12.5, "v_th": 1.05 } },
    { "id": "out",  "kind": "probe", "params": { "target": "pop1", "type": "spike_rate", "window_ms": 10.0 } }
  ],
  "edges": [
    { "src": "pop0", "dst": "pop1", "weight": 0.25, "delay_us": 500 }
  ],
  "probes": [
    { "id": "p_spike", "target": "pop1", "type": "spike", "window_us": 0 }
  ]
}
```

Example 2 — Event vision kernel with delay line (exact-event)

```json
{
  "version": "0.1.0",
  "profile": "REALTIME",
  "seed": 7,
  "time": { "unit": "us", "mode": "exact_event", "epsilon_time_us": 50, "epsilon_numeric": 1e-5 },
  "graph": { "name": "vision_optical_flow" },
  "nodes": [
    { "id": "flow", "kind": "kernel", "op": "optical_flow_events", "params": { "win_us": 5000 } },
    { "id": "delay", "kind": "delay_line", "params": { "buf_us": 2000 } },
    { "id": "probe_flow", "kind": "probe", "params": { "target": "flow", "type": "custom" } }
  ],
  "edges": [
    { "src": "flow", "dst": "delay", "delay_us": 200 }
  ],
  "probes": [
    { "id": "p_flow", "target": "flow", "type": "custom", "window_us": 10000 }
  ],
  "security": { "sandbox": true, "rate_limit_keps": 2000, "overflow_policy": "drop_tail" }
}
```

Validation guidance
- Validate with the schema above (JSON). For YAML sources, convert to JSON prior to validation.
- Enforce topological constraints (acyclic or well-formed feedback loops via delay lines).
- Verify that any operator listed in `op` is available in the target backend or has a declared fallback (see [docs/specs/dcd.schema.md](docs/specs/dcd.schema.md)).

Interoperability and packaging
- EIR JSON is included as `eir.json` in EFPKG; see [docs/specs/efpkg.schema.md](docs/specs/efpkg.schema.md).
- Probes should match the outputs referenced by golden traces (Event Tensor JSONL) in EFPKG.

Change log
- 0.1.0: Initial EIR schema and examples.