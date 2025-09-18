# Backend Architecture and Plugin Interface — Specification v0.1

Status: Normative specification for EventFlow Neuromorphic Execution Layer (NEL) backends. Defines plugin contracts, discovery, capability negotiation, planning, determinism obligations, and reference simulators.

Related specifications
- EIR IR: [docs/specs/eir.schema.md](docs/specs/eir.schema.md)
- Device Capability Descriptor (DCD): [docs/specs/dcd.schema.md](docs/specs/dcd.schema.md)
- Event Tensor: [docs/specs/event_tensor.schema.md](docs/specs/event_tensor.schema.md)
- Packaging (EFPKG): [docs/specs/efpkg.schema.md](docs/specs/efpkg.schema.md)
- Determinism and replay: [docs/DETERMINISM.md](docs/DETERMINISM.md)
- Conformance: [docs/CONFORMANCE.md](docs/CONFORMANCE.md)

Goals
- Provide a uniform, deterministic execution interface for hardware backends and simulators.
- Enable automatic capability negotiation and graceful fallback to emulation when needed.
- Ensure trace capture and equivalence across backends within declared epsilons.

Scope
- Plugin discovery and lifecycle
- DCD schema usage and validation
- Planning: mapping, partitioning, placement, and scheduling
- Execution: run, pause, stop, profile, and trace
- Simulators: cpu-sim (reference) and gpu-sim (feature-flagged)
- Error model and fallback policies

---

## 1. Plugin discovery and lifecycle

1.1. Discovery
- Backends are Python packages exposing an entry point group, e.g., `eventflow.backends` → module path.
- Each backend package must contain a static DCD JSON (e.g., `dcd.json`) validated against [docs/specs/dcd.schema.md](docs/specs/dcd.schema.md).

1.2. Registration
- Backend registers a unique backend `name` (e.g., `cpu-sim`, `gpu-sim`, `neuro-asic-x1`), semantic `version`, and an optional `family` (e.g., `Simulator`, `Loihi`, `SpiNNaker`).

1.3. Lifecycle
- initialize(config) → backend handle with immutable DCD snapshot
- plan(eir, requirements?) → plan object (see Section 3)
- run(plan, inputs, probes, seed) → execution handle
- stop(handle), close() → release resources

Backends MUST be stateless across `plan()` invocations for determinism and reproducibility; any necessary caches must be keyed by DCD/version.

---

## 2. Capability descriptors (DCD) and negotiation

2.1. DCD compliance
- The backend MUST ship a DCD validated by [docs/specs/dcd.schema.md](docs/specs/dcd.schema.md).
- The backend MUST document deterministic modes: `exact_event`, `fixed_step`, or both.

2.2. Negotiation inputs
- EIR IR (validated) and optional `capabilities_required` subset from EFPKG manifest (see [docs/specs/efpkg.schema.md](docs/specs/efpkg.schema.md)).

2.3. Negotiation algorithm (required behavior)
- Validate profile compatibility: `profile ∈ conformance_profiles`.
- Normalize timing: align EIR `time.unit` to device `time_resolution_ns`; compute quantization error; ensure EIR `epsilon_time_us` bound.
- Opset coverage: ensure `nodes[*].op` and `kind` are supported per `supported_ops`, `neuron_models`, `plasticity_rules`. For gaps:
  - Prefer emulation on the same backend if declared (soft kernels).
  - Else partition to emulator (cpu-sim) transparently (hybrid plan).
- Capacity: respect `limits` (max_neurons, max_synapses, fanin/fanout), `memory` budgets, and `topology` constraints by partitioning and placement.
- Overflow and rate policies: ensure requested policies are supported; otherwise propose substitutions with warnings.

2.4. Output
- A `plan` object describing:
  - partitions, placement, and interconnect routing (if applicable),
  - schedules and timing mode (exact-event or fixed-step with `dt`),
  - emulation subgraphs (if any) and their assigned emulator backend,
  - expected epsilons and notes,
  - warnings and errors.

---

## 3. Plan object (normative fields)

A plan MUST be a JSON-serializable dictionary with at least:

- `backend`: { `name`, `version`, `mode`: "exact_event"|"fixed_step", `dt_us`? }
- `graph`: { `id`, `profile`, `seed` }
- `partitions`: array of
  - { `id`, `nodes`: [node_ids], `placement`: { `chip`?, `core`? }, `resources`: { neurons, synapses, memory_kib }, `emulated`: boolean }
- `routes` (optional for multi-chip): array of
  - { `src_partition`, `dst_partition`, `max_hops`, `bandwidth_meps`, `latency_us` }
- `schedule`: array of
  - { `partition_id`, `policy`: "event"|"fixed", `dt_us`?, `priority`, `affinity` }
- `probes`: array mapping EIR probes to backend counters or DMA streams
- `epsilons`: { `time_us`, `numeric` }
- `warnings`: array of strings
- `notes`: string

Plans MUST be deterministic given the same (EIR, DCD, seed).

---

## 4. Execution interface

4.1. Run
- `run(plan, inputs, probes, seed)` starts execution and returns a handle.
- Inputs: zero or more Event Tensor JSONL streams (paths or iterators), validated by [docs/specs/event_tensor.schema.md](docs/specs/event_tensor.schema.md).
- Probes: names or descriptors from EIR and plan; the backend MUST map to its internal measurement points.

4.2. Control
- `pause(handle)`, `resume(handle)`, `stop(handle)`; operations MUST be idempotent.

4.3. Outputs
- Golden trace capture: JSONL probe records ordered per [Determinism](docs/DETERMINISM.md).
- Telemetry: JSONL profile records (latency, throughput, drops, power proxy).
- Return status: success/failure with diagnostics.

4.4. Determinism obligations
- For `exact_event`, the backend MUST process events in strictly increasing timestamp order with a stable tie-breaker.
- For `fixed_step`, the backend MUST use the declared `dt_us` and ensure bounded drift within `epsilons.time_us`.
- All stochastic behavior MUST derive from the provided `seed`.

---

## 5. Reference simulators

5.1. cpu-sim (reference)
- Modes: `exact_event` and `fixed_step` (deterministic).
- Time resolution: 1 µs (`time_resolution_ns = 1000`).
- Supported ops: at least `lif`, `synapse_exp`, `delay_line`, `probe_spike`, and core domain kernels (e.g., `conv2d_events`).
- Power: proxy values (0 for energy accounting unless model supplied).

5.2. gpu-sim (feature-flagged)
- Mode: deterministic `fixed_step` only.
- Time resolution: 0.5 µs preferred; quantization as needed.
- Opset: superset of cpu-sim where feasible; identical semantics for overlapping ops.
- Determinism: kernel launch order and reductions MUST produce stable results across runs with the same seed.

---

## 6. Error model and fallback

Standard error codes:
- `backend.unsupported_profile`
- `backend.unsupported_op`
- `backend.capacity_exceeded`
- `backend.unsupported_policy` (overflow/rate)
- `backend.time_quantization_violation`
- `backend.execution_failed`

Fallback policy:
- The registry MUST attempt emulation (cpu-sim) for unsupported ops or capacity overflow, preserving global determinism and epsilon bounds. If fallback violates constraints, fail with actionable diagnostics.

---

## 7. Testing and conformance

Backends MUST pass the Conformance Suite (see [docs/CONFORMANCE.md](docs/CONFORMANCE.md)):
- Trace equivalence against golden within epsilons
- Latency distributions (P50/P99) within profile constraints
- Drop rate and overflow policy adherence
- Power proxy reporting where applicable

Plans and runs SHOULD be reproducible and serializable for audit and regression testing.

Change log
- 0.1.0: Initial backend plugin interface, DCD negotiation rules, plan schema, execution obligations, and simulator requirements.