# Conformance and Quality Assurance — Specification v0.1

Status: Normative requirements for validating correctness, determinism, performance, safety, and packaging of EventFlow artifacts and backends.

Related specifications
- EIR IR schema: [docs/specs/eir.schema.md](docs/specs/eir.schema.md)
- Event Tensor schema: [docs/specs/event_tensor.schema.md](docs/specs/event_tensor.schema.md)
- DCD capability schema: [docs/specs/dcd.schema.md](docs/specs/dcd.schema.md)
- Packaging (EFPKG): [docs/specs/efpkg.schema.md](docs/specs/efpkg.schema.md)
- Determinism & replay: [docs/DETERMINISM.md](docs/DETERMINISM.md)
- Backends & planning: [docs/BACKENDS.md](docs/BACKENDS.md)
- SAL: [docs/SAL.md](docs/SAL.md)

Purpose
- Ensure that EventFlow applications run reproducibly across simulators and hardware backends with deterministic semantics.
- Provide standardized test procedures, datasets, and pass/fail criteria for profiles (BASE, REALTIME, LEARNING, LOWPOWER).
- Enable compatibility badges and a model hub matrix based on objective measurements.

Scope
- Artifact validation (schemas and packaging)
- Functional correctness (trace equivalence to golden)
- Determinism (bit-exact on same backend; epsilon-equivalence cross-backend)
- Performance (latency, throughput, drop rate)
- Safety & security policies (overflow, rate limits, sandbox)
- SAL ingestion correctness (ordering, units, sync, anomaly detection)
- Backend capability & planning constraints (DCD compliance)

---

## 1. Profiles and pass/fail criteria

1.1. BASE profile
- Determinism: Bit-exact on the same backend (seeded). Cross-backend within epsilons.
- Epsilons: time epsilon ≤ 100 µs; numeric epsilon ≤ 1e-5 relative (default; apps may tighten).
- Overflow policy: must match EIR/security settings.
- Minimum: compile on at least one backend (cpu-sim).

1.2. REALTIME profile
- Determinism: real-time scheduling guarantees; fixed-step or exact-event per DCD.
- Epsilons: time epsilon ≤ 50 µs recommended; numeric epsilon ≤ 1e-5.
- Latency budgets: P99 end-to-end latency ≤ declared profile constraint (e.g., 10 ms).
- Overflow policy: block may be forbidden; drop policy must be honored with counters.

1.3. LEARNING profile (v0.1 placeholder)
- Plasticity rules must match DCD semantics; convergence tests are informational in v0.1.
- Determinism is evaluated on stochastic seeds and fixed datasets; acceptance is epsilon-equivalence of observable probe metrics.

1.4. LOWPOWER profile (informational in v0.1)
- Energy-per-event proxy reporting required when available; otherwise simulated estimates.
- Must meet BASE criteria; power thresholds are comparative vs. baseline.

---

## 2. Test categories

2.1. Schema & packaging validation
- Validate EIR JSON against [docs/specs/eir.schema.md](docs/specs/eir.schema.md).
- Validate Event Tensor streams (inputs/traces) against [docs/specs/event_tensor.schema.md](docs/specs/event_tensor.schema.md).
- Validate EFPKG manifest against [docs/specs/efpkg.schema.md](docs/specs/efpkg.schema.md).
- Validate DCDs for all selected backends against [docs/specs/dcd.schema.md](docs/specs/dcd.schema.md).

2.2. Trace equivalence (golden comparison)
- Procedure:
  1) Select a golden backend (cpu-sim by default).
  2) Run the EIR with specified seed and inputs; capture golden JSONL probe traces.
  3) Run candidate backend with same seed and inputs; capture candidate traces.
  4) Merge-scan and compare:
     - Timing: |ts_out - ts_ref| ≤ epsilon_time_us
     - Numeric: |val_out - val_ref| / max(1, |val_ref|) ≤ epsilon_numeric
- Pass/Fail:
  - PASS if all probes meet timing and numeric epsilons with no record count mismatch.
  - FAIL otherwise; report first divergence and summary metrics.

2.3. Determinism (same-backend reproducibility)
- Re-run candidate backend N≥3 times with identical EIR, seed, inputs.
- Expect bit-identical traces; if not, FAIL with diagnostics (ordering, RNG, floats).

2.4. Performance metrics
- Latency:
  - Measure per-probe end-to-end latency distribution (P50/P95/P99).
  - REALTIME: enforce P99 ≤ budget (e.g., 10 ms).
- Throughput: events/sec measured at SAL ingress and backend egress.
- Drop rate: percentage of dropped records; must match overflow policy expectations.

2.5. SAL ingestion tests
- Ordering: outputs must be strictly non-decreasing in ts after sync.
- Units: headers must declare units; values consistent within tolerance.
- Sync: drift/jitter bounded; report sync_status (drift_ppm, jitter_ns).
- Safety: counters for dropped_head, dropped_tail, blocked_time_ms.
- Spoofing: inject anomalies; SAL must flag per policy.

2.6. Backend capability & planning
- Check profile support in DCD (profile ∈ conformance_profiles).
- Ensure opset coverage; unsupported ops must be emulated or produce a planning error.
- Capacity & memory: planning must respect limits; hybrid plans acceptable.

2.7. Security & sandbox
- If custom kernels are allowed, verify sandbox enforcement and configured resource limits.
- Negative tests: attempt to exceed rate limits or memory; require clean failure and logs.

---

## 3. Metrics and telemetry

3.1. Telemetry schema
- JSONL records with fields: ts_ms, metric, value, labels (backend, partition, probe, etc.).
- Examples: "latency_ms", "events_per_sec", "dropped_pct", "power_mw".

3.2. Aggregation
- Summaries computed by the CLI (ef profile): count, avg, min, max, P50, P95, P99 if available.

3.3. Power reporting
- For simulators: proxy values or “unavailable”.
- For hardware: use device counters if exposed; otherwise informational.

---

## 4. Datasets and goldens (v0.1)

Included small samples (for smoke tests)
- examples/events/vision_sample.jsonl — DVS-like events
- examples/events/audio_sample.jsonl — STFT band events

User-provided datasets
- Place under a local path and reference in EFPKG traces/inputs.
- For reproducible benchmarks (e.g., NeuroBench-like), publish checksums and licensing.

---

## 5. CLI workflow (ef validate)

5.1. Inputs
- Path to EFPKG or separate: EIR JSON, inputs JSONL, profile, seed, backends list.

5.2. Steps
1) Validate schemas (EIR, inputs, DCD, EFPKG if given).
2) Plan and run golden backend; capture golden traces.
3) For each target backend:
   - Plan and run; capture candidate traces and telemetry.
   - Compare against golden; compute performance metrics.
4) Emit summary JSON and a human-readable report.

5.3. Outputs
- run.json: environment, versions, backends, seed, hashes.
- metrics.json: latency, throughput, drops, power proxy.
- equivalence.json: per-probe pass/fail and first divergence details.
- logs/: backend logs and SAL counters.

---

## 6. Pass/Fail decisions

- A backend PASS requires:
  - Schema validation PASS.
  - Determinism PASS (same-backend reproducibility).
  - Equivalence PASS (within epsilons).
  - REALTIME (if applicable): P99 latency within budget.
  - Overflow policy adherence and safety counters present.
- Otherwise FAIL with actionable diagnostics.

---

## 7. Diagnostics and reporting

- On failure, report:
  - First divergence (probe id, index, ts_ref, ts_out, delta_ts, val_ref, val_out, delta_val).
  - Aggregate mismatch counts and worst deltas.
  - Offending policies (e.g., overflow mismatch) and remediation suggestions.

- Attach:
  - EIR, DCD, plan.json, run.json, telemetry JSONL, checksums and hashes.

---

## 8. Compatibility badges

- Backends and EFPKGs can earn badges:
  - BASE/REALTIME/LEARNING/LOWPOWER
  - “Deterministic” (bit-exact same-backend)
  - “Cross-backend Equivalent” (across listed backends)
  - “Latency P99 ≤ X ms” (profile-dependent)
- Badges are recorded in the hub compatibility matrix.

---

## 9. Change management

- All conformance tests MUST be versioned with the SDK and schemas.
- Golden traces MUST include the EIR hash, inputs hash, plan hash, and SDK version.
- Breaking changes to schemas or test procedures require a major version bump.

---

## 10. Minimal conformance checklist (summary)

- [ ] EIR validates
- [ ] Inputs validate and SAL produces deterministic Event Tensors
- [ ] DCD validates; profile supported
- [ ] Golden run captured with hashes
- [ ] Candidate deterministic across runs
- [ ] Equivalence within epsilons
- [ ] REALTIME latency P99 ≤ budget
- [ ] Overflow policy obeyed; counters emitted
- [ ] Packaging manifests correct; checksums consistent

Change log
- 0.1.0: Initial conformance and QA specification.