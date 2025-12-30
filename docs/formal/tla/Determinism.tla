------------------------------ MODULE Determinism ------------------------------
EXTENDS Naturals, Integers, Sequences, FiniteSets, TLC, Types

(*
  Determinism.tla — Same-backend determinism and cross-backend equivalence (v0.1)

  Scope:
    - SameBackendDet: With identical EIR, inputs, and seed on the same backend, the
      observable probe outputs (traces) are bit-identical (modeled as exact equality).
    - CrossBackendEq: With identical EIR, inputs, and seed across two backends, the
      observable probe outputs are equivalent within declared epsilons (time, numeric).
    - Assumptions: SALOrdering and Merge invariants hold upstream (canonical order).
    - Pairing: 1:1 pairing by index after canonical sort (no insertion/deletion in v0.1).

  Variables:
    outA, outB : sequences of events (probe outputs) from two runs.
    equalPlan  : boolean indicating both runs use identical backend and plan.
    sameSeed   : boolean indicating both runs use identical global seed.
    sameInput  : boolean indicating both runs use identical inputs (after SAL).
    mode       : "same" | "cross" determines which property should hold.

  Usage:
    - TLC/Apalache models provide bounded sequences for outA/outB and booleans for assumptions.
    - For mode="same", require SameBackendDet.
    - For mode="cross", require CrossBackendEq.
*)

CONSTANTS
    Mode \* "same" | "cross"

ASSUME Mode \in {"same","cross"}

VARIABLES outA, outB, equalPlan, sameSeed, sameInput

IsEventSeq(s) == s \in Seq([ts: Nat, idx: Seq(Nat), val: Int, src: STRING, ing: Nat])

Init ==
  /\ outA \in Seq([ts: Nat, idx: Seq(Nat), val: Int, src: STRING, ing: Nat])
  /\ outB \in Seq([ts: Nat, idx: Seq(Nat), val: Int, src: STRING, ing: Nat])
  /\ CanonicalNonDecreasing(outA)
  /\ CanonicalNonDecreasing(outB)
  /\ equalPlan \in BOOLEAN
  /\ sameSeed  \in BOOLEAN
  /\ sameInput \in BOOLEAN

(*
  We treat this as a safety-only spec: state is fixed by Init, Next stutters.
*)
Next ==
  /\ UNCHANGED << outA, outB, equalPlan, sameSeed, sameInput >>

Spec == Init /\ [][Next]_<<outA, outB, equalPlan, sameSeed, sameInput>>

(***************************************************************************)
(* Properties                                                              *)
(***************************************************************************)

(*
  Same-backend determinism: exact equality (bit-identical) when plan/seed/input are identical.
  Note: In implementation, floating-point determinism is ensured via fixed reductions per backend.
*)
SameBackendPre ==
  /\ Mode = "same"
  /\ equalPlan = TRUE
  /\ sameSeed  = TRUE
  /\ sameInput = TRUE

SameBackendDet ==
  SameBackendPre => outA = outB

(*
  Cross-backend epsilon-equivalence: same length and PairwiseClose under epsilons,
  when inputs and seed are the same (plans allowed to differ across backends).
*)
CrossBackendPre ==
  /\ Mode = "cross"
  /\ sameSeed  = TRUE
  /\ sameInput = TRUE

CrossBackendEq ==
  CrossBackendPre => (
    /\ Len(outA) = Len(outB)
    /\ PairwiseClose(outA, outB)
  )

(***************************************************************************)
(* Invariants and Theorems                                                 *)
(***************************************************************************)

TypeInv ==
  /\ IsEventSeq(outA)
  /\ IsEventSeq(outB)
  /\ CanonicalNonDecreasing(outA)
  /\ CanonicalNonDecreasing(outB)

THEOREM TypeOK ==
  Spec => []TypeInv

THEOREM SameBackendDeterminism ==
  Spec => []SameBackendDet

THEOREM CrossBackendEquivalence ==
  Spec => []CrossBackendEq

=============================================================================
\* End of Determinism.tla