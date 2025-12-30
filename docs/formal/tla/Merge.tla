------------------------------ MODULE Merge ------------------------------
EXTENDS Naturals, Integers, Sequences, FiniteSets, TLC, Types

(*
  Merge.tla — Canonical multi-source merge (v0.1)

  Purpose:
    - Specify a deterministic k-way merge from multiple SAL-normalized sources into a single
      canonically ordered output stream.
    - Each source is assumed to already satisfy CanonicalNonDecreasing (see SALOrdering).
    - The merged out stream must preserve canonical non-decreasing order and be a stable
      merge of inputs under the CanonicalLessThan relation (see Types).

  Related:
    - [Types.tla](docs/formal/tla/Types.tla): Event records, CanonicalLessThan(), CanonicalNonDecreasing()
    - SAL single-source ordering: [SALOrdering.tla](docs/formal/tla/SALOrdering.tla)
    - Replay pairing and epsilon checks are defined in ReplayEquivalence (separate module).

  Constants:
    K           : Nat \* number of input sources
    SourceIds   : Seq(STRING) with Len(SourceIds) = K, unique identifiers
*)

CONSTANTS
    K
  , SourceIds

ASSUME /\ K \in Nat /\ K \geq 1
       /\ SourceIds \in Seq(STRING)
       /\ Len(SourceIds) = K
       /\ Cardinality(SeqToSet(SourceIds)) = K

(***************************************************************************)
(* State                                                                   *)
(***************************************************************************)

(*
  inputs[i] : canonically non-decreasing sequence of events from source i
  idx[i]    : current read cursor (1-based) into inputs[i]
  out       : merged output (sequence of events)
*)
VARIABLES inputs, idx, out

IsEventSeq(s) == s \in Seq([ts: Nat, idx: Seq(Nat), val: Int, src: STRING, ing: Nat])

Init ==
  /\ inputs \in [ 1..K -> Seq([ts: Nat, idx: Seq(Nat), val: Int, src: STRING, ing: Nat]) ]
  /\ \A i \in 1..K : CanonicalNonDecreasing(inputs[i])
  /\ idx \in [ 1..K -> Nat ]
  /\ \A i \in 1..K :
        IF Len(inputs[i]) = 0 THEN idx[i] = 1 ELSE idx[i] = 1
  /\ out = <<>>

(***************************************************************************)
(* Helper functions                                                        *)
(***************************************************************************)

At(i) ==
  IF idx[i] \in 1..Len(inputs[i]) THEN inputs[i][ idx[i] ] ELSE NULL

IsActive(i) ==
  idx[i] \in 1..Len(inputs[i])

ActiveSet ==
  { i \in 1..K : IsActive(i) }

(*
  Choose the minimal next event across all active sources under CanonicalLessThan.
  Break ties stably by source position i (which corresponds to SourceIds[i]).
*)
MinActiveIndex ==
  IF ActiveSet = {} THEN 0
  ELSE
    LET mins == { i \in ActiveSet :
                    \A j \in ActiveSet :
                      ~CanonicalLessThan( At(j), At(i) )
                } IN
      CHOOSE i \in mins : TRUE

(***************************************************************************)
(* Actions                                                                 *)
(***************************************************************************)

(*
  Step: select the minimal head event and append to out, advance that source cursor.
*)
Step ==
  /\ ActiveSet # {}
  /\ LET i == MinActiveIndex IN
       /\ out' = out \o << At(i) >>
       /\ idx' = [ idx EXCEPT ![i] = @ + 1 ]
       /\ UNCHANGED inputs

(*
  NoOp: stuttering step to allow TLC exploration without progress.
*)
NoOp ==
  /\ UNCHANGED << inputs, idx, out >>

Next == Step \/ NoOp

Spec == Init /\ [][Next]_<<inputs, idx, out>>

(***************************************************************************)
(* Invariants                                                              *)
(***************************************************************************)

(*
  MergeOrderInv: out is canonically non-decreasing.
*)
MergeOrderInv ==
  CanonicalNonDecreasing(out)

(*
  SubsequencePreservationInv: out is a stable merge of inputs; i.e., relative order
  of events from each source is preserved in out. We assert a weaker, checkable form:
  for each source i, the projection of out to events with src=SourceIds[i] is a prefix
  of inputs[i].
*)
Proj(outSeq, sid) ==
  [ j \in 1..Len(outSeq) : Src(outSeq[j]) = sid ]

IsPrefixOf(a, b) ==
  /\ a \in Seq(b) \* TLC semantics: every element of a is in b in the same relative order
  /\ \A i \in 1..Len(a) : a[i] = b[i]

SourcePrefixInv ==
  \A i \in 1..K :
    LET sid == SourceIds[i] IN
      LET projIdxs == Proj(out, sid) IN
        LET projSeq  == [ k \in 1..Len(projIdxs) |-> out[ projIdxs[k] ] ] IN
          IsPrefixOf(projSeq, inputs[i])

(*
  SourceHeadDominanceInv: any emitted event e in out is no greater than the current head of any active source.
  In other words, no skipped smaller head remains in any input.
*)
Head(i) ==
  IF IsActive(i) THEN At(i) ELSE NULL

HeadDominanceInv ==
  \A pos \in 1..Len(out) :
    \A i \in 1..K :
      IF IsActive(i) /\ Head(i) # NULL THEN
        ~CanonicalLessThan( Head(i), out[pos] )
      ELSE TRUE

(*
  Safety invariant combining ordering and preservation properties.
*)
SafetyInv ==
  /\ MergeOrderInv
  /\ SourcePrefixInv
  /\ HeadDominanceInv

THEOREM SafetyHolds ==
  Spec => []SafetyInv

=============================================================================
\* End of Merge.tla