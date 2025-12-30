------------------------------ MODULE Types ------------------------------
EXTENDS Naturals, Integers, Sequences, FiniteSets, TLC

(*
  Types.tla — Core datatypes and relations for EventFlow determinism (v0.1)
  Scope:
    - Event record type and helper accessors
    - Canonical ordering relation (strict) and non-decreasing constraint
    - Replay equivalence epsilon checks (time, numeric absolute)
    - Pairwise closeness predicate for traces
  Notes:
    - We model numeric values as integers for v0.1 to keep TLC exploration simple.
      Extend to Reals or fixed-point later if needed.
    - idx is a finite sequence of Nat (primary element idx[1] when present).
    - ing is a per-source stable ingestion ordinal used as a final tie-breaker.
*)

(***************************************************************************)
(* Constants (provided by a model or tool config)                          *)
(***************************************************************************)
CONSTANTS
    EpsTimeUS      \* Nat, absolute timing epsilon in microseconds (&#62;= 0)
  , EpsNumericAbs  \* Nat, absolute numeric epsilon (&#62;= 0)

ASSUME EpsTimeUS \in Nat /\ EpsNumericAbs \in Nat

(***************************************************************************)
(* Core record and helper projections                                      *)
(***************************************************************************)

(*
Event record fields:
  ts  : Nat               \* timestamp in declared time.unit (us for SAL)
  idx : Seq(Nat)          \* spatial/channel tuple (may be empty for scalars)
  val : Int               \* value or coded payload (integer for v0.1)
  src : STRING            \* source identifier (e.g., "audio.mic", "vision.dvs")
  ing : Nat               \* ingestion order (stable, monotonically increasing per source)
*)
IsEvent(e) ==
  /\ e \in [ts: Nat, idx: Seq(Nat), val: Int, src: STRING, ing: Nat]
  /\ (Len(e.idx) \geq 0)

Ts(e)   == e.ts
Idx(e)  == e.idx
Val(e)  == e.val
Src(e)  == e.src
Ing(e)  == e.ing

(***************************************************************************)
(* Canonical ordering (strict)                                             *)
(***************************************************************************)

(*
  CanonicalLessThan(e1, e2) encodes the total tie-breaking order:
    1) Primary: ts ascending
    2) Secondary: first idx element ascending if both have length \ge 1
    3) Tertiary: remaining idx tuple lexicographic ascending
    4) Quaternary: ingestion order (stable, ascending)
*)
LexiDiffIndex(i1, i2) ==
  LET mset == { i \in 1..Min(Len(i1), Len(i2)) : i1[i] # i2[i] } IN
    IF mset = {} THEN 0 ELSE CHOOSE k \in mset: TRUE

IdxLexiLess(i1, i2) ==
  LET k == LexiDiffIndex(i1, i2) IN
    IF k = 0 THEN Len(i1) < Len(i2)   \* equal prefix; shorter is less
    ELSE i1[k] < i2[k]

CanonicalLessThan(e1, e2) ==
  \/ Ts(e1) < Ts(e2)
  \/ /\ Ts(e1) = Ts(e2)
     /\ (
           \/ /\ Len(Idx(e1)) \ge 1 /\ Len(Idx(e2)) \ge 1 /\ Idx(e1)[1] < Idx(e2)[1]
           \/ /\ (Len(Idx(e1)) = 0 \/ Len(Idx(e2)) = 0) /\ IdxLexiLess(Idx(e1), Idx(e2))
           \/ /\ Idx(e1) = Idx(e2) /\ Ing(e1) < Ing(e2)
        )

(*
  CanonicalNonDecreasing(seq) holds when the sequence is sorted by the
  non-strict canonical order (i.e., never descending under CanonicalLessThan).
*)
CanonicalNonDecreasing(seq) ==
  /\ seq \in Seq( [ts: Nat, idx: Seq(Nat), val: Int, src: STRING, ing: Nat] )
  /\ \A i \in 1..Max(0, Len(seq)-1) :
        ~CanonicalLessThan(seq[i+1], seq[i])

(***************************************************************************)
(* Replay equivalence epsilon checks (absolute epsilons in v0.1)           *)
(***************************************************************************)

ReplayTimeClose(tout, tref) ==
  IF tout \geq tref THEN (tout - tref) \leq EpsTimeUS
  ELSE (tref - tout) \leq EpsTimeUS

ReplayNumericClose(vout, vref) ==
  Abs(vout - vref) \leq EpsNumericAbs

(*
  Pairwise closeness for two equal-length event sequences.
  NOTE: This does not perform pairing search; sequences must be aligned 1:1
  and sorted canonically upstream (per Determinism and Comparator).
*)
RECURSIVE PairwiseClose(_, _)
PairwiseClose(out, ref) ==
  /\ out \in Seq( [ts: Nat, idx: Seq(Nat), val: Int, src: STRING, ing: Nat] )
  /\ ref \in Seq( [ts: Nat, idx: Seq(Nat), val: Int, src: STRING, ing: Nat] )
  /\ Len(out) = Len(ref)
  /\ \A i \in 1..Len(out) :
        /\ ReplayTimeClose(Ts(out[i]), Ts(ref[i]))
        /\ ReplayNumericClose(Val(out[i]), Val(ref[i]))

(***************************************************************************)
(* Simple sanity lemmas (placeholders; discharge in Apalache invariants)   *)
(***************************************************************************)

(*
  If a sequence is canonically non-decreasing, then any contiguous subsequence
  is also canonically non-decreasing. This is used in merge proofs.
*)
RECURSIVE Slice(_, _, _)
Slice(s, lo, hi) ==
  IF lo &#62; hi THEN <<>> ELSE SubSeq(s, lo, hi)

Lemma_SubseqNonDecreasing ==
  \A s \in Seq( [ts: Nat, idx: Seq(Nat), val: Int, src: STRING, ing: Nat] ):
    CanonicalNonDecreasing(s) =>
      \A lo, hi \in Nat :
        /\ 1 \leq lo /\ lo \leq hi /\ hi \leq Len(s)
        => CanonicalNonDecreasing(Slice(s, lo, hi))

=============================================================================
\* End of Types.tla