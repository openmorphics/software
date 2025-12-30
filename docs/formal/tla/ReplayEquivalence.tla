------------------------------ MODULE ReplayEquivalence ------------------------------
EXTENDS Naturals, Integers, Sequences, FiniteSets, TLC, Types

(*
  ReplayEquivalence.tla — Pairing and epsilon-based replay equivalence (v0.1)

  Purpose:
    - Specify when two probe output traces are considered equivalent for conformance:
        * Same length and 1:1 pairing under canonical alignment
        * Timing within EpsTimeUS
        * Numeric within EpsNumericAbs (v0.1 absolute; relative can be added later)
    - Provide an abstract comparator state machine that reads "golden" and "candidate"
      streams and asserts PairwiseClose (from Types).

  Related:
    - Canonical order and event record types: [Types](docs/formal/tla/Types.tla:1)
    - Determinism semantics and epsilons: [docs/DETERMINISM.md](docs/DETERMINISM.md)
    - CLI comparator behavior: [eventflow-cli/ef.py](eventflow-cli/ef.py:1)

  Notes:
    - We assume inputs are already canonically sorted (SAL and Merge invariants hold).
    - Pairing is by index (1..N) after canonical sort; no insertion/deletion alignment in v0.1.
*)

(***************************************************************************)
(* State                                                                   *)
(***************************************************************************)

VARIABLES golden, candidate, i, verdict

IsEventSeq(s) == s \in Seq([ts: Nat, idx: Seq(Nat), val: Int, src: STRING, ing: Nat])

Init ==
  /\ golden   \in Seq([ts: Nat, idx: Seq(Nat), val: Int, src: STRING, ing: Nat])
  /\ candidate \in Seq([ts: Nat, idx: Seq(Nat), val: Int, src: STRING, ing: Nat])
  /\ CanonicalNonDecreasing(golden)
  /\ CanonicalNonDecreasing(candidate)
  /\ Len(golden) = Len(candidate)
  /\ i = 1
  /\ verdict = "undecided"  \* "pass" | "fail" | "undecided"

(***************************************************************************)
(* Helper Predicates                                                       *)
(***************************************************************************)

WithinEpsAt(j) ==
  /\ ReplayTimeClose( Ts(candidate[j]), Ts(golden[j]) )
  /\ ReplayNumericClose( Val(candidate[j]), Val(golden[j]) )

(***************************************************************************)
(* Actions                                                                 *)
(***************************************************************************)

StepOK ==
  /\ verdict = "undecided"
  /\ i \in 1..Len(golden)
  /\ WithinEpsAt(i)
  /\ i' = i + 1
  /\ IF i = Len(golden) THEN verdict' = "pass" ELSE verdict' = verdict
  /\ UNCHANGED << golden, candidate >>

StepFail ==
  /\ verdict = "undecided"
  /\ i \in 1..Len(golden)
  /\ ~WithinEpsAt(i)
  /\ verdict' = "fail"
  /\ i' = i
  /\ UNCHANGED << golden, candidate >>

Stutter ==
  /\ verdict # "undecided"
  /\ UNCHANGED << golden, candidate, i, verdict >>

Next == StepOK \/ StepFail \/ Stutter

Spec == Init /\ [][Next]_<<golden, candidate, i, verdict>>

(***************************************************************************)
(* Invariants and Outcomes                                                 *)
(***************************************************************************)

AlignedLengths ==
  Len(golden) = Len(candidate)

CanonicalInputs ==
  /\ CanonicalNonDecreasing(golden)
  /\ CanonicalNonDecreasing(candidate)

NoOutOfBounds ==
  /\ verdict = "undecided" => i \in 1..Len(golden)
  /\ verdict # "undecided" => TRUE

SafetyInv ==
  /\ IsEventSeq(golden) /\ IsEventSeq(candidate)
  /\ AlignedLengths
  /\ CanonicalInputs
  /\ NoOutOfBounds

THEOREM SafetyHolds ==
  Spec => []SafetyInv

(*
  Liveness (if all pairs are within eps, comparator eventually passes).
  In TLC we encode this as: if StepFail never enabled, verdict reaches "pass".
*)
AllWithinEps ==
  \A j \in 1..Len(golden) : WithinEpsAt(j)

PassesWhenAllWithin ==
  AllWithinEps => <> (verdict = "pass")

=============================================================================
\* End of ReplayEquivalence.tla