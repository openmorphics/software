# EventFlow Device Capability Descriptor (DCD) — JSON Schema and Examples v0.1

Status: Normative schema draft for backend/device capability advertisement used by capability negotiation and automatic backend selection.

Purpose
- Advertise timing granularity, deterministic modes, opset coverage, memory and routing limits, and power characteristics.
- Enable compile-time mapping and graceful fallback with explicit epsilon contracts.
- Standardize conformance profile support (BASE, REALTIME, LEARNING, LOWPOWER).

Scope
- Defines the JSON Schema for DCD.
- Specifies required and optional fields and validation constraints.
- Provides example descriptors for cpu-sim (reference), gpu-sim (accelerated), and a hypothetical neuromorphic ASIC.

Negotiation overview (high level)
- Validate EIR profile against `conformance_profiles`.
- Normalize EIR timing to `time_resolution_ns`; compute quantization error; ensure `epsilon_time_us` bounds.
- Check `supported_ops`, `neuron_models`, `plasticity_rules` coverage; select software emulation for gaps.
- Partition by `max_neurons`, `max_synapses`, `memory` constraints; plan routing under `topology`.
- Emit warnings when constraints are unmet; suggest `fixed_step` if `exact_event` cannot be guaranteed.

JSON Schema (Draft 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "EventFlow Device Capability Descriptor (DCD)",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "name",
    "vendor",
    "family",
    "version",
    "time_resolution_ns",
    "deterministic_modes",
    "supported_ops",
    "conformance_profiles"
  ],
  "properties": {
    "name": { "type": "string", "minLength": 1 },
    "vendor": { "type": "string", "minLength": 1 },
    "family": { "type": "string", "minLength": 1 },
    "version": { "type": "string", "minLength": 1 },

    "deterministic_modes": {
      "type": "array",
      "minItems": 1,
      "items": { "enum": ["exact_event", "fixed_step"] },
      "description": "Execution modes supported with deterministic semantics"
    },

    "supported_ops": {
      "type": "array",
      "minItems": 1,
      "items": { "type": "string" },
      "description": "Operator names supported by this device or backend (e.g., lif, glif, synapse_exp, stdp, conv2d_events, pooling_events)"
    },

    "opset_versions": {
      "type": "object",
      "additionalProperties": { "type": "string" },
      "description": "Optional map op_name -> semantic version of operator support"
    },

    "neuron_models": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Supported neuron model identifiers (e.g., LIF, GLIF, Izhikevich, AdEx)"
    },

    "plasticity_rules": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Supported online learning rules (e.g., STDP, Hebbian)"
    },

    "weight_precisions_bits": {
      "type": "array",
      "items": { "type": "integer", "minimum": 1 },
      "description": "Permitted weight quantizations in bits"
    },

    "state_precisions_bits": {
      "type": "array",
      "items": { "type": "integer", "minimum": 1 },
      "description": "Permitted state variable quantizations (e.g., membrane potentials)"
    },

    "time_resolution_ns": {
      "type": "integer",
      "minimum": 1,
      "description": "Smallest scheduling tick/granularity in nanoseconds"
    },

    "max_jitter_ns": {
      "type": "integer",
      "minimum": 0,
      "description": "Upper bound on event scheduling jitter under load (if known)"
    },

    "clock": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "drift_ppm": { "type": "number", "minimum": 0 },
        "sync_method": { "enum": ["free_running", "ptp", "ntp", "host_sync", "other"] },
        "deterministic_fixed_step_only": { "type": "boolean", "default": false }
      }
    },

    "limits": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "max_neurons": { "type": "integer", "minimum": 1 },
        "max_synapses": { "type": "integer", "minimum": 1 },
        "max_fanout": { "type": "integer", "minimum": 1 },
        "max_fanin": { "type": "integer", "minimum": 1 },
        "min_delay_us": { "type": "integer", "minimum": 0 },
        "max_delay_us": { "type": "integer", "minimum": 0 }
      }
    },

    "memory": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "per_core_kib": { "type": "integer", "minimum": 1 },
        "per_chip_mib": { "type": "integer", "minimum": 1 },
        "global_mib": { "type": "integer", "minimum": 1 }
      }
    },

    "topology": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "multi_chip": { "type": "boolean", "default": false },
        "cores_per_chip": { "type": "integer", "minimum": 1 },
        "max_hops": { "type": "integer", "minimum": 0 },
        "router_bandwidth_meps": { "type": "number", "minimum": 0, "description": "Mega-events per second" },
        "link_latency_us": { "type": "number", "minimum": 0 }
      }
    },

    "power": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "mw_per_spike_typ": { "type": "number", "minimum": 0 },
        "idle_mw": { "type": "number", "minimum": 0 },
        "tdp_mw": { "type": "number", "minimum": 0 }
      }
    },

    "features": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "on_chip_learning": { "type": "boolean" },
        "stochastic_neurons": { "type": "boolean" },
        "analog_dynamics": { "type": "boolean" },
        "kernel_sandbox": { "type": "boolean", "description": "Backend enforces sandbox for custom kernels" }
      }
    },

    "overflow_behavior": { "enum": ["drop_head", "drop_tail", "block"] },

    "conformance_profiles": {
      "type": "array",
      "minItems": 1,
      "items": { "enum": ["BASE", "REALTIME", "LEARNING", "LOWPOWER"] }
    },

    "notes": { "type": "string" }
  }
}
```

Validation guidelines
- Vendors SHOULD specify precise `time_resolution_ns`, `max_jitter_ns`, and clock drift where measurable.
- When only `fixed_step` is deterministic, set `clock.deterministic_fixed_step_only=true` and include `deterministic_modes=["fixed_step"]`.
- Use `opset_versions` to communicate subtle semantic differences.

Example — cpu-sim (reference backend)

```json
{
  "name": "cpu-sim",
  "vendor": "EventFlow",
  "family": "Simulator",
  "version": "0.1.0",
  "time_resolution_ns": 1000,
  "max_jitter_ns": 0,
  "deterministic_modes": ["exact_event", "fixed_step"],
  "supported_ops": ["lif", "synapse_exp", "delay_line", "probe_spike", "conv2d_events"],
  "opset_versions": { "lif": "1.0.0", "synapse_exp": "1.0.0" },
  "neuron_models": ["LIF"],
  "plasticity_rules": [],
  "weight_precisions_bits": [8, 16, 32],
  "state_precisions_bits": [16, 32],
  "clock": { "drift_ppm": 0, "sync_method": "host_sync", "deterministic_fixed_step_only": false },
  "limits": { "max_neurons": 10000000, "max_synapses": 100000000, "max_fanout": 100000, "max_fanin": 100000, "min_delay_us": 0, "max_delay_us": 100000000 },
  "memory": { "per_core_kib": 1048576, "per_chip_mib": 16384, "global_mib": 16384 },
  "topology": { "multi_chip": false, "cores_per_chip": 32, "max_hops": 0, "router_bandwidth_meps": 1000, "link_latency_us": 0 },
  "power": { "mw_per_spike_typ": 0.0, "idle_mw": 0.0, "tdp_mw": 0.0 },
  "features": { "on_chip_learning": false, "stochastic_neurons": false, "analog_dynamics": false, "kernel_sandbox": true },
  "overflow_behavior": "drop_tail",
  "conformance_profiles": ["BASE", "REALTIME"],
  "notes": "Deterministic by construction with seeded RNG and canonical ordering."
}
```

Example — gpu-sim (accelerated simulator)

```json
{
  "name": "gpu-sim",
  "vendor": "EventFlow",
  "family": "Simulator",
  "version": "0.1.0",
  "time_resolution_ns": 500,
  "max_jitter_ns": 0,
  "deterministic_modes": ["fixed_step"],
  "supported_ops": ["lif", "synapse_exp", "delay_line", "probe_spike", "conv2d_events", "pool_events"],
  "neuron_models": ["LIF"],
  "plasticity_rules": [],
  "weight_precisions_bits": [8, 16, 32],
  "state_precisions_bits": [16, 32],
  "clock": { "drift_ppm": 0, "sync_method": "host_sync", "deterministic_fixed_step_only": true },
  "limits": { "max_neurons": 5000000, "max_synapses": 250000000, "max_fanout": 131072, "max_fanin": 131072, "min_delay_us": 0, "max_delay_us": 50000000 },
  "memory": { "per_core_kib": 262144, "per_chip_mib": 24576, "global_mib": 24576 },
  "topology": { "multi_chip": false, "cores_per_chip": 80, "max_hops": 0, "router_bandwidth_meps": 2000, "link_latency_us": 0.5 },
  "power": { "mw_per_spike_typ": 0.05, "idle_mw": 5000.0, "tdp_mw": 250000.0 },
  "features": { "on_chip_learning": false, "stochastic_neurons": false, "analog_dynamics": false, "kernel_sandbox": true },
  "overflow_behavior": "drop_tail",
  "conformance_profiles": ["BASE", "REALTIME"],
  "notes": "Deterministic fixed-step execution only; exact-event equivalence holds within epsilon time bounds."
}
```

Example — hypothetical neuromorphic ASIC

```json
{
  "name": "neuro-asic-x1",
  "vendor": "AcmeSilicon",
  "family": "XSeries",
  "version": "1.0",
  "time_resolution_ns": 50,
  "max_jitter_ns": 100,
  "deterministic_modes": ["exact_event", "fixed_step"],
  "supported_ops": ["lif", "glif", "synapse_exp", "synapse_alpha", "delay_line", "probe_spike"],
  "opset_versions": { "lif": "1.1.0", "synapse_exp": "1.0.0" },
  "neuron_models": ["LIF", "GLIF"],
  "plasticity_rules": ["STDP"],
  "weight_precisions_bits": [4, 8],
  "state_precisions_bits": [8, 16],
  "clock": { "drift_ppm": 10, "sync_method": "ptp", "deterministic_fixed_step_only": false },
  "limits": { "max_neurons": 2000000, "max_synapses": 200000000, "max_fanout": 4096, "max_fanin": 4096, "min_delay_us": 1, "max_delay_us": 2000000 },
  "memory": { "per_core_kib": 128, "per_chip_mib": 512, "global_mib": 512 },
  "topology": { "multi_chip": true, "cores_per_chip": 4096, "max_hops": 8, "router_bandwidth_meps": 750, "link_latency_us": 2.0 },
  "power": { "mw_per_spike_typ": 0.001, "idle_mw": 50.0, "tdp_mw": 5000.0 },
  "features": { "on_chip_learning": true, "stochastic_neurons": true, "analog_dynamics": true, "kernel_sandbox": false },
  "overflow_behavior": "drop_head",
  "conformance_profiles": ["BASE", "REALTIME", "LEARNING", "LOWPOWER"],
  "notes": "Exact-event mode is deterministic with bounded jitter; event-time epsilon must account for router contention."
}
```

Conformance implications
- Devices MUST publish a DCD included in packaging manifests and used for compatibility matrices.
- REALTIME profile assertions MUST be testable in the Conformance Suite (latency/jitter bounds).
- LEARNING profile devices MUST document plasticity rule semantics and default parameter ranges.

Change log
- 0.1.0: Initial DCD schema and examples.