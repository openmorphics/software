# Determinism and Replay — Specification v0.1

Status: Normative requirements for deterministic execution, reproducible replay, and cross-backend equivalence.

Related specifications
- EIR IR schema: [docs/specs/eir.schema.md](docs/specs/eir.schema.md)
- Event Tensor schema: [docs/specs/event_tensor.schema.md](docs/specs/event_tensor.schema.md)
- Backends and planning: [docs/BACKENDS.md](docs/BACKENDS.md)
- Conformance suite: [docs/CONFORMANCE.md](docs/CONFORMANCE.md)

Goals
- Bit-exact reproducibility on the same backend given identical EIR, inputs, and seed.
- Cross-backend equivalence within declared time and numeric epsilons.
- Unit-checked temporal operations and canonical event ordering across the stack.

Scope
- Execution modes and time model
- Canonical ordering and tie-breakers
- Random number generation (RNG) and state seeding
- Floating-point determinism and reductions
- Trace capture and replay procedures
- Cross-backend equivalence definition
- Diagnostics and failure reporting

---

## 1. Execution modes and time model

Modes (declared in EIR.time; see [docs/specs/eir.schema.md](docs/specs/eir.schema.md))
- exact_event
  - Events processed strictly in non-decreasing timestamp order.
  - Ties broken deterministically (Section 2).
  - No implicit resampling; operators must be pure functions of prior events and their state.
- fixed_step
  - Discretize time with dt = fixed_step_dt_us; event effects are applied on step boundaries.
  - Quantization error is tracked; drift must be bounded within epsilon_time_us.
  - Operators may be step-driven; internal accumulators updated once per step.

Units
- time.unit is global (ns|us|ms). SAL and backends MUST convert to this unit before scheduling.
- Delays and constraints (e.g., refractory_us) must be coherent with time.unit.

Epsilons (from EIR.time)
- epsilon_time_us: Maximum allowed absolute timing deviation for cross-backend equivalence.
- epsilon_numeric: Relative numeric tolerance for value comparisons (e.g., voltages, rates).

---

## 2. Canonical ordering (ties and ingestion)

Canonical order (strict)
1) Primary: timestamp ts ascending
2) Secondary: channel or first spatial index (idx[0]) ascending if applicable
3) Tertiary: remaining idx tuple lexicographic ascending
4) Quaternary: ingestion order (stable)

Requirements
- SAL MUST output event streams in canonical order (post-sync); bounded reorder buffers are allowed but MUST not reorder beyond jitter bounds.
- Backends MUST preserve canonical order for all internal queues that affect user-visible probes.
- For fused streams (multi-sensor), the runtime MUST merge by canonical order under a shared timebase.

---

## 3. Random number generation (RNG)

Global seed
- EIR.seed is a 64-bit unsigned integer shared across the graph.

Per-operator streams
- Each operator derives a deterministic sub-seed using a stable hash of (EIR.seed, graph.name, node.id, op-specific-scope).
- Counter-based RNG (e.g., Philox) MUST be used to avoid order dependence; sampling MUST be indexable.

Reproducibility
- The same EIR, inputs, and seed MUST produce identical traces on the same backend across runs.
- Backends MUST not incorporate nondeterministic sources (e.g., system time, thread race) into computation.

---

## 4. Floating-point determinism

Same-backend determinism
- For CPU simulators: use well-defined reduction orders and disable fused-multiply-add unless fixed in implementation.
- For GPU simulators: deterministic kernels MUST use fixed warp/block-level reduction orders and disable non-deterministic atomics; compile with deterministic math flags where applicable.

Cross-backend equivalence
- Exact bitwise equality is NOT required; numeric equivalence MUST hold within epsilon_numeric (relative) and a small absolute tolerance when values are near zero (recommended 1e-12).

Quantization and precision
- Backends that quantize weights/states MUST document the precision (see DCD weight/state precisions) and contribute to equivalence checks via declared epsilons.

---

## 5. Trace capture and replay

Trace format
- Probes MUST output JSON Lines (JSONL) with records that conform to an Event Tensor-like record:
  - ts (integer), id or target (string), metric/type (string), value(s) (number or object)
- For spike outputs: (ts, neuron_index or location, val=1) is acceptable; for rates/voltages: aggregate windows or per-step values.

Golden trace
- A golden trace is produced by a designated reference backend and seed.
- Golden trace MUST include a header line with metadata (sdk version, eir hash, seed, profile).

Replay
- Given an EIR, inputs, and golden trace, replay mode compares backend outputs against golden:
  - Timing equivalence: |ts_out - ts_ref| ≤ epsilon_time_us
  - Numeric equivalence: |val_out - val_ref| / max(1, |val_ref|) ≤ epsilon_numeric

Ordering
- Output probe records MUST be sorted per canonical order (Section 2). Replayers can merge-scan both streams efficiently.

Diagnostics
- On first mismatch, report:
  - probe id, event index, ts_out, ts_ref, delta_ts, val_out, val_ref, delta_val
  - local context window (±N events)
- Also summarize total mismatches, worst-case deltas, and pass/fail.

---

## 6. Cross-backend equivalence definition

Definition
- Two runs are equivalent if for every probe they produce an output sequence that can be paired 1:1 such that:
  - Count match: same number of records (unless declared drop policies differ; see below).
  - Timing: per-record timing deviation within epsilon_time_us.
  - Numeric: per-record value deviation within epsilon_numeric relative tolerance (and small absolute epsilon near zero).

Dropped events
- If a backend legitimately drops events due to configured overflow policy, it MUST emit counters and annotate probes with drop statistics.
- For conformance profiles that permit drops, equivalence is measured on the retained subset after policy alignment; otherwise dropping is a failure.

Hybrid plans
- For composite plans (emulation + device), equivalence rules apply to the composite outputs; internal partitioning need not be visible.

---

## 7. Scheduling determinism

Threading and concurrency
- Parallel execution MUST not change the observable order of events and probe outputs.
- Use stable work partitioning keyed by (node.id, partition.id).

Timers and host interaction
- Real-time backends MUST not depend on wall-clock time for any computation path that affects probe values; time only informs scheduling boundaries and must be quantized as specified.

Checkpointing
- Checkpoints MUST include all operator states and RNG counters to allow exact resume and deterministic continuation.
- Checkpoints SHOULD include a short rolling window of recent events to resume canonical ordering after restart.

---

## 8. Hashing and content-addressability

EIR hash
- Compute a stable content hash over the EIR JSON (normalized, whitespace-stripped) plus version and profile; include in trace headers and EFPKG manifest.

Inputs hash
- For recorded inputs, compute a hash over the input JSONL(s) and include in trace headers; for live inputs, this is omitted or replaced with a session id.

Plan hash
- Backends SHOULD include a hash of the executable plan; this supports auditability and regression testing.

---

## 9. Failure modes and remediation

Common failures
- Order violations: events out-of-order due to insufficient reorder buffer; increase buffer or adjust jitter bounds.
- Timing drift: epsilon_time_us exceeded; switch to fixed_step or refine synchronization.
- Numeric drift: floating-point nondeterminism; enforce deterministic reductions or relax epsilon_numeric with justification.
- Drop policy mismatch: configure identical overflow policies across runs.

Remediation guidance
- Emit actionable messages with suggested configuration changes.
- Include per-probe and per-partition counters to assist root-cause analysis.

---

## 10. Minimal determinism checklist (backends)

- [ ] Declares deterministic modes and time resolution in DCD.
- [ ] Implements canonical ordering and stable merges.
- [ ] Uses counter-based RNG with per-operator streams derived from global seed.
- [ ] Provides deterministic CPU/GPU kernel options.
- [ ] Emits golden trace headers with EIR/inputs/plan hashes.
- [ ] Provides replay tooling to compare against golden within epsilons.

Change log
- 0.1.0: Initial determinism and replay specification.