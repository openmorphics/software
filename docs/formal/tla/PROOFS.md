# EventFlow TLA+ Proof Obligations — v0.1

Scope
- This document enumerates the proof obligations for the TLA+ modules:
  - [Types.tla](docs/formal/tla/Types.tla:1)
  - [SALOrdering.tla](docs/formal/tla/SALOrdering.tla:1)
  - [Merge.tla](docs/formal/tla/Merge.tla:1)
  - [ReplayEquivalence.tla](docs/formal/tla/ReplayEquivalence.tla:1)
  - [Determinism.tla](docs/formal/tla/Determinism.tla:1)
- Each obligation identifies:
  - Property name (invariant, theorem, or liveness)
  - Assumptions/preconditions
  - Actions covered (for inductive checks)
  - Model-check recipe (TLC/Apalache), including bounded domains and constants
  - Link to runtime assertion mapping in planned executable contracts: [eventflow-core/conformance/contracts.py](eventflow-core/conformance/contracts.py:1)

Notation
- “Inv preserved by A” means: Init |= Inv and Inv ∧ A ⇒ Inv’ (standard inductive invariant proof).
- We rely on TLC/Apalache to discharge obligations at bounded sizes appropriate for v0.1.

1) Types.tla
1.1 CanonicalNonDecreasing(seq) well-formedness
- Property: Sequences produced by SAL and Merge satisfy CanonicalNonDecreasing.
- Covered by: Higher-level modules; Types provides the predicate only.

1.2 PairwiseClose(out, ref) totality on equal-length event sequences
- Assumptions: Len(out) = Len(ref); both are event sequences.
- Obligation: Safety lemma that PairwiseClose is defined and checks (no OOB).
- Recipe: Checked indirectly in [ReplayEquivalence.tla](docs/formal/tla/ReplayEquivalence.tla:1) “SafetyHolds”.

1.3 Lemma_SubseqNonDecreasing (sanity)
- Statement: Any contiguous subsequence of a canonically non-decreasing sequence is also canonically non-decreasing.
- Actions: None (pure lemma).
- Recipe: Validate via Apalache invariant assertions at small bounds (optional).

2) SALOrdering.tla
2.1 CanonicalOrderInv (ordering)
- Property: outQ is CanonicalNonDecreasing
- Actions: Ingest, EmitMin, BlockStep, NoOp
- Assumptions: JitterBoundUS ∈ Nat; MaxBuf ∈ Nat; OverflowPolicy ∈ {drop_head|drop_tail|block}; Sources ⊆ STRING
- Obligation: Inv preserved by each action; EmitMin chooses canonical minimum.
- Recipe (TLC): Small bounded domains:
  - EpsTimeUS ∈ {0, 50, 100}; EpsNumericAbs ∈ {0, 1}
  - JitterBoundUS ∈ {0, 50, 100}; MaxBuf ∈ {2, 3, 4}
  - OverflowPolicy ∈ {"drop_head","drop_tail","block"}
  - Event fields domains: ts ∈ 0..5; idx ∈ sequences of length ≤ 2 with elements 0..1; val ∈ -1..1; ing ∈ 0..5
- Mapping to runtime: Enforced by contracts in [eventflow-core/conformance/contracts.py](eventflow-core/conformance/contracts.py:1) applied in SAL emit paths ([eventflow-sal/eventflow_sal/sync/clock.py](eventflow-sal/eventflow_sal/sync/clock.py:1), [eventflow-sal/eventflow_sal/util/ring.py](eventflow-sal/eventflow_sal/util/ring.py:1)).

2.2 BufferPolicyInv (safety)
- Property: Len(buf) ≤ MaxBuf; counters in Nat; policy in expected set.
- Actions: Ingest (with/without overflow), EmitMin, BlockStep, NoOp
- Obligation: Inductive preservation across all actions.
- Recipe: Same TLC bounds as 2.1.

2.3 StableSrcInv (per-source monotone ingestion)
- Property: For each source s, Ing is non-decreasing in outQ; Src(outQ) ⊆ Sources and Src(buf) ⊆ Sources.
- Actions: Ingest, EmitMin
- Obligation: Inductive preservation.
- Recipe: TLC bounds with 2–3 sources (Sources subset of {"A","B","C"}).

2.4 Liveness (WF on EmitMin)
- Property: With weak fairness on EmitMin (WF_vars(EmitMin)), and if buffer non-empty infinitely often, outQ grows.
- Actions: EmitMin
- Obligation: Model-run verification with fairness enabled (FairSpec).
- Recipe: TLC with WF enabled; bounded runs to observe progress; Apalache optional.

3) Merge.tla
3.1 MergeOrderInv (ordering)
- Property: out is CanonicalNonDecreasing
- Actions: Step (k-way minimal advance), NoOp
- Assumptions: Each inputs[i] CanonicalNonDecreasing
- Obligation: Inductive preservation.
- Recipe: TLC with K ∈ {2,3}, inputs[i] length ≤ 3.

3.2 SourcePrefixInv (per-source order preserved)
- Property: Projection of out by src is a prefix of inputs[i]
- Actions: Step
- Obligation: Inductive preservation and tie consistency.
- Recipe: Same as 3.1.

3.3 HeadDominanceInv (no smaller head skipped)
- Property: No head of any active source is canonically smaller than any emitted element in out
- Actions: Step
- Obligation: Inductive preservation.
- Recipe: Same as 3.1.

4) ReplayEquivalence.tla
4.1 SafetyHolds (comparator safety)
- Property: AlignedLengths ∧ CanonicalInputs ∧ NoOutOfBounds
- Actions: StepOK, StepFail, Stutter
- Assumptions: Canonical inputs; equal length
- Obligation: Inductive preservation; no OOB on i.
- Recipe: TLC with short sequences (length ≤ 4), varying EpsTimeUS and EpsNumericAbs.

4.2 PassesWhenAllWithin (liveness)
- Property: If all pairs are within eps, eventually verdict = "pass"
- Actions: StepOK
- Obligation: Progress in bounded runs.
- Recipe: TLC simulation with AllWithinEps true.

5) Determinism.tla
5.1 SameBackendDeterminism
- Property: If equalPlan ∧ sameSeed ∧ sameInput and Mode="same", then outA = outB
- Actions: None (stutter spec)
- Assumptions: CanonicalNonDecreasing(outA/outB)
- Obligation: Theorem holds under preconditions.
- Recipe: TLC checks with Mode="same", varied sequences that must be equal.

5.2 CrossBackendEquivalence
- Property: If sameSeed ∧ sameInput and Mode="cross", then Len(outA)=Len(outB) ∧ PairwiseClose(outA,outB)
- Actions: None (stutter spec)
- Assumptions: CanonicalNonDecreasing(outA/outB)
- Obligation: Theorem holds under preconditions.
- Recipe: TLC checks with Mode="cross", generate pairs within eps; negative cases assert theorem does not force equality.

Implementation verification mapping
- SAL ordering assertions:
  - Enforce CanonicalNonDecreasing at emission boundaries in [eventflow-sal/eventflow_sal/sync/clock.py](eventflow-sal/eventflow_sal/sync/clock.py:1) and buffer transitions in [eventflow-sal/eventflow_sal/util/ring.py](eventflow-sal/eventflow_sal/util/ring.py:1).
- Merge correctness:
  - Implement stable k-way merge preserving per-source order; assert MergeOrderInv and SourcePrefixInv in contracts.
- Comparator correctness:
  - Implement eps-based comparator mirroring [ReplayEquivalence.tla](docs/formal/tla/ReplayEquivalence.tla:1), with first divergence diagnostics; expose via CLI compare-traces in [eventflow-cli/ef.py](eventflow-cli/ef.py:1).
- Determinism toggles:
  - EF_DETERMINISM_CHECKS=1 enables runtime contracts and raises on violations.
  - Epsilons overridable via CLI flags; defaults from EIR time.epsilon_*.

Model checking configs (planned under docs/formal/tla/models)
- Types.cfg (sanity)
- SALOrdering-ExactEvent.cfg and SALOrdering-FixedStep.cfg
- Merge.cfg
- Replay.cfg
- Determinism-Same.cfg and Determinism-Cross.cfg

Make targets (planned)
- make tlc-sal, make tlc-merge, make tlc-replay, make tlc-det
  - Emit reports to docs/formal/tla/out/

Exit criteria for v0.1
- All listed invariants verified by TLC/Apalache within bounded models.
- Runtime contracts enforce the same properties on executable code paths.
- Pytest suite demonstrates violations are caught and conformant pipelines pass with the wakeword example.