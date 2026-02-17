# EventFlow Formal Specification (TLA+) — v0.1

Scope (approved)
- TLA+-only core determinism for SAL ordering, canonical merges, and replay equivalence.
- Model checking via TLC/Apalache with bounded configurations.
- Executable Python runtime assertions and pytest derived from the invariants (to be added).
- Initial target example: wakeword pipeline and Event Tensor inputs.

Modules
- Types: core datatypes and relations.
  - File: [Types.tla](docs/formal/tla/Types.tla:1)
  - Provides:
    - Event record predicate IsEvent.
    - CanonicalLessThan and CanonicalNonDecreasing (ordering).
    - ReplayTimeClose, ReplayNumericClose, and PairwiseClose (equivalence).
- SALOrdering: single-source SAL sync and canonical ordering with overflow policies.
  - File: [SALOrdering.tla](docs/formal/tla/SALOrdering.tla:1)
  - Provides:
    - State machine for ingest → reorder buffer → canonical emit.
    - Invariants: CanonicalOrderInv, BufferPolicyInv, StableSrcInv, SafetyInv.
- Merge: canonical multi-source k-way merge.
  - File: [Merge.tla](docs/formal/tla/Merge.tla:1)
  - Provides:
    - Merging logic across already-ordered sources.
    - Invariants: MergeOrderInv, SourcePrefixInv, HeadDominanceInv, SafetyInv.
- ReplayEquivalence: epsilon-based pairing comparator for golden vs candidate traces.
  - File: [ReplayEquivalence.tla](docs/formal/tla/ReplayEquivalence.tla:1)
  - Provides:
    - Step-wise comparator, PairwiseClose checks, pass/fail decision.
- Determinism: same-backend determinism and cross-backend epsilon-equivalence.
  - File: [Determinism.tla](docs/formal/tla/Determinism.tla:1)
  - Provides:
    - Theorems SameBackendDeterminism and CrossBackendEquivalence under assumptions.

Preconditions and Postconditions (formalized via guards and invariants)
- SAL (single-source)
  - Pre:
    - Inputs normalized to a common time unit per spec (see [docs/SAL.md](docs/SAL.md:1)).
    - Bounded jitter ≤ JitterBoundUS and buffer capacity MaxBuf modeled as constants.
    - OverflowPolicy ∈ {drop_head, drop_tail, block}.
  - Post:
    - Emitted outQ is CanonicalNonDecreasing.
    - Buffer length ≤ MaxBuf; counters consistent with policy (BufferPolicyInv).
    - Per-source ingestion ordinal non-decreasing (StableSrcInv).
- Merge (multi-source)
  - Pre:
    - Each inputs[i] is CanonicalNonDecreasing (output of SALOrdering or equivalent).
  - Post:
    - out is CanonicalNonDecreasing (MergeOrderInv).
    - Per-source order preserved: projection is a prefix of inputs[i] (SourcePrefixInv).
    - No smaller head remains un-emitted (HeadDominanceInv).
- Replay comparator
  - Pre:
    - golden and candidate are CanonicalNonDecreasing and equal length.
  - Post:
    - verdict ∈ {pass, fail}; if all pairs within eps → eventually pass.
- Determinism
  - Same-backend:
    - Pre: equalPlan ∧ sameSeed ∧ sameInput ∧ Mode="same".
    - Post: outA = outB (bit-identical).
  - Cross-backend:
    - Pre: sameSeed ∧ sameInput ∧ Mode="cross".
    - Post: PairwiseClose(outA, outB) and equal length.

Invariants summary
- Types
  - CanonicalNonDecreasing(seq)
  - PairwiseClose(out, ref)
- SALOrdering
  - CanonicalOrderInv ∧ BufferPolicyInv ∧ StableSrcInv ⇒ SafetyInv
- Merge
  - MergeOrderInv ∧ SourcePrefixInv ∧ HeadDominanceInv ⇒ SafetyInv
- ReplayEquivalence
  - SafetyHolds: aligned lengths, canonical inputs, in-bounds stepping.
- Determinism
  - TypeOK, SameBackendDeterminism, CrossBackendEquivalence.

Proof obligations (overview)
- Inductive invariance:
  - SAL: SafetyInv preserved by Ingest, EmitMin, BlockStep.
  - Merge: SafetyInv preserved by Step.
  - Replay: SafetyHolds preserved by StepOK, StepFail, Stutter.
- Determinism:
  - SameBackendDeterminism under SameBackendPre.
  - CrossBackendEquivalence under CrossBackendPre.
- Progress/fairness:
  - Weak fairness on EmitMin suffices to avoid deadlock with perpetual inputs in SAL.

Full list and model checking recipes are tracked in [PROOFS.md](docs/formal/tla/PROOFS.md:1) (to be authored).

Model checking (to be scripted)
- TLC (unbounded logic, explicit state):
  - Provide .cfg files with constants:
    - EpsTimeUS, EpsNumericAbs, JitterBoundUS, MaxBuf, OverflowPolicy, Mode, K, SourceIds.
  - Typical bounds:
    - Small event domains (ts∈0..N, idx length ≤ 2, buf length ≤ 3–5).
- Apalache (symbolic model checking, types and invariants):
  - Provide type annotations via configuration and run invariants at higher bounds.

Executable mapping to code
- SAL output ordering and sync:
  - [eventflow-sal/eventflow_sal/sync/clock.py](eventflow-sal/eventflow_sal/sync/clock.py:1)
  - [eventflow-sal/eventflow_sal/util/ring.py](eventflow-sal/eventflow_sal/util/ring.py:1)
  - [eventflow-sal/eventflow_sal/open.py](eventflow-sal/eventflow_sal/open.py:1)
- Comparator and conformance:
  - [eventflow-cli/ef.py](eventflow-cli/ef.py:1) (compare-traces entrypoint and validators)
  - Comparator module: [eventflow-core/eventflow_core/conformance/comparator.py](eventflow-core/eventflow_core/conformance/comparator.py:1)
- Runtime determinism contracts (planned):
  - [eventflow-core/conformance/contracts.py](eventflow-core/conformance/contracts.py:1)
- CLI switch/flags (planned):
  - [eventflow-cli/ef.py](eventflow-cli/ef.py:1) (EF_DETERMINISM_CHECKS, epsilon overrides)

Verification procedures (high level)
1) SAL single-source ordering:
   - Generate small synthetic streams (bounded jitter) and check CanonicalOrderInv via runtime contracts.
   - Model check [SALOrdering.tla](docs/formal/tla/SALOrdering.tla:1) with TLC/Apalache configs.
2) Merge:
   - Compose multiple ordered streams; verify merged output is canonically non-decreasing and preserves per-source order.
   - Model check [Merge.tla](docs/formal/tla/Merge.tla:1).
3) Replay equivalence:
   - Compare golden vs candidate traces within epsilons; inspect first divergence.
   - Model check [ReplayEquivalence.tla](docs/formal/tla/ReplayEquivalence.tla:1).
4) Determinism:
   - Same-backend: simulate identical plan/seed/input; require exact equality.
   - Cross-backend: require PairwiseClose within epsilons.
   - Model check [Determinism.tla](docs/formal/tla/Determinism.tla:1).

Planned artifacts (next commits)
- [PROOFS.md](docs/formal/tla/PROOFS.md:1) — proof obligations and how they are discharged.
- models/ — TLC and Apalache configs (ExactEvent.cfg, FixedStep.cfg, Merge.cfg, Replay.cfg, Determinism.cfg).
- Makefile targets for tlc/apalache runs (outputs to out/).
- Python contracts and tests:
  - Unit tests for canonical ordering, merge, and comparator.
  - Property-based tests (Hypothesis) for small bounded models.
  - End-to-end wakeword conformance within eps.

References
- Determinism spec: [docs/DETERMINISM.md](docs/DETERMINISM.md:1)
- SAL spec: [docs/SAL.md](docs/SAL.md:1)
- Conformance: [docs/CONFORMANCE.md](docs/CONFORMANCE.md:1)
- CLI: [docs/CLI.md](docs/CLI.md:1)
- EIR schema: [docs/specs/eir.schema.md](docs/specs/eir.schema.md:1)
