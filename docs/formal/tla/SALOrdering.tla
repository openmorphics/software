------------------------------ MODULE SALOrdering ------------------------------
EXTENDS Naturals, Integers, Sequences, FiniteSets, TLC, Types

(*
  SALOrdering.tla — SAL synchronization and deterministic ordering state machine (v0.1)

  Purpose:
    - Model SAL ingestion with bounded jitter reordering into a canonical, non-decreasing output.
    - Capture overflow policies: drop_head, drop_tail, block.
    - Provide invariants aligned with docs/DETERMINISM.md Sections 1–3 and docs/SAL.md Sections 3–4.
    - Serve as the foundation for multi-source merge (separate module) and replay equivalence.

  Imports:
    - Types.tla provides Event records and CanonicalLessThan / CanonicalNonDecreasing,
      as well as Replay* predicates and helpers.

  Constants (provided by model configs):
    JitterBoundUS   : Nat       \* maximum expected arrival jitter absorbed by reorder buffer
    MaxBuf          : Nat       \* maximum buffer length (bounded memory/safety)
    OverflowPolicy  : STRING    \* "drop_head" | "drop_tail" | "block"
    Sources         : SUBSET STRING \* admissible source ids
    EpsTimeUS, EpsNumericAbs come from Types.

  Notes:
    - We model a single-source SAL path here; multi-source canonical merge is specified in Merge.tla.
    - Mode selection (exact_event vs fixed_step) influences admissible inputs but ordering constraints remain identical.
*)

CONSTANTS
    JitterBoundUS
  , MaxBuf
  , OverflowPolicy
  , Sources

ASSUME /\ JitterBoundUS \in Nat
       /\ MaxBuf \in Nat
       /\ OverflowPolicy \in {"drop_head","drop_tail","block"}
       /\ Sources \subseteq STRING

(***************************************************************************)
(* Variables and State                                                     *)
(***************************************************************************)

(*
  inQ    : sequence of Events as observed from device/file after timestamp normalization
  buf    : bounded reorder buffer (sequence) storing not-yet-emitted Events
  outQ   : emitted Events (sequence), must be canonically non-decreasing
  t0     : watermark (Nat) of the minimal ts that must already be emitted
  cnt    : counters record for safety accounting
*)
VARIABLES inQ, buf, outQ, t0, cnt

IsEventSeq(s) == s \in Seq( [ts: Nat, idx: Seq(Nat), val: Int, src: STRING, ing: Nat] )

Counters == [ produced      : Nat,
              dropped_head  : Nat,
              dropped_tail  : Nat,
              blocked_steps : Nat ]

Init ==
  /\ inQ  = <<>>
  /\ buf  = <<>>
  /\ outQ = <<>>
  /\ t0   = 0
  /\ cnt  = [ produced |-> 0, dropped_head |-> 0, dropped_tail |-> 0, blocked_steps |-> 0 ]

(***************************************************************************)
(* Helper predicates                                                       *)
(***************************************************************************)

(*
  MayEmit(e, t0): we can emit e if its timestamp is no less than watermark t0
  and any event that could still arrive within jitter bounds would not precede it.
  In this single-source model, we approximate by: emit the minimum element in buf
  under CanonicalLessThan, and advance t0 accordingly.
*)
MinByCanonical(seq) ==
  IF Len(seq) = 0 THEN <<>> ELSE
    LET S == { i \in 1..Len(seq) : \A j \in 1..Len(seq) : ~(CanonicalLessThan(seq[j], seq[i])) }
    IN CHOOSE k \in S : TRUE

IsMinByCanonical(e, seq) ==
  /\ e \in SetToSeq(SeqToSet(seq)) \* e must be from seq
  /\ \A x \in SetToSeq(SeqToSet(seq)) : ~CanonicalLessThan(x, e)

Append(x, s) == AppendSeq(<<x>>, s)  \* prepend element x to sequence s
PushBack(s, x) == s \o <<x>>
PopAtIndex(s, i) == SubSeq(s, 1, i-1) \o SubSeq(s, i+1, Len(s))

BufNotFull == Len(buf) < MaxBuf

(*
  CanonicalInsert simply enqueues to buf; we rely on MinByCanonical to emit min-first.
  For model checking tractability, we do not maintain buf sorted, only outQ.
*)

(***************************************************************************)
(* Actions                                                                 *)
(***************************************************************************)

(*
  Ingest: a new Event arrives from the source with stable src, ing; SAL
  accepts it into buf subject to overflow policy.
*)
CanIngest(e) ==
  /\ IsEvent(e)
  /\ Src(e) \in Sources
  /\ BufNotFull \/ OverflowPolicy # "block"

OverflowDropHead ==
  /\ ~BufNotFull
  /\ OverflowPolicy = "drop_head"

OverflowDropTail ==
  /\ ~BufNotFull
  /\ OverflowPolicy = "drop_tail"

OverflowBlock ==
  /\ ~BufNotFull
  /\ OverflowPolicy = "block"

ChooseIngressEvent(e) ==
  \E s \in Sources, ts \in Nat, val \in Int, idx \in Seq(Nat), ing \in Nat :
    e = [ts |-> ts, idx |-> idx, val |-> val, src |-> s, ing |-> ing]

Ingest ==
  \E e \in [ts: Nat, idx: Seq(Nat), val: Int, src: STRING, ing: Nat] :
    /\ ChooseIngressEvent(e)  \* unconstrained generator bounded by TLC config
    /\ CanIngest(e)
    /\ IF BufNotFull THEN
         /\ buf' = PushBack(buf, e)
         /\ cnt' = [cnt EXCEPT !.produced = @ + 1]
       ELSE
         /\ IF OverflowDropHead THEN
               /\ buf' = PushBack(SubSeq(buf, 2, Len(buf)), e)
               /\ cnt' = [cnt EXCEPT !.produced = @ + 1, !.dropped_head = @ + 1]
            ELSE IF OverflowDropTail THEN
               /\ buf' = buf
               /\ cnt' = [cnt EXCEPT !.dropped_tail = @ + 1]
            ELSE \* block
               /\ buf' = buf
               /\ cnt' = [cnt EXCEPT !.blocked_steps = @ + 1]
    /\ UNCHANGED << inQ, outQ, t0 >>

(*
  EmitMin: emit the canonical minimum from buf to outQ, ensuring outQ remains canonically
  non-decreasing. Advance t0 to at least the emitted ts (could be tightened with jitter logic).
*)
EmitMin ==
  /\ Len(buf) \ge 1
  /\ LET i == MinByCanonical(buf) IN
       LET e == buf[i] IN
         /\ outQ' = PushBack(outQ, e)
         /\ buf'  = PopAtIndex(buf, i)
         /\ t0'   = Max(t0, Ts(e))
         /\ UNCHANGED inQ
         /\ cnt' = cnt

(*
  BlockStep: represent a stuttering step where no action can be taken (e.g., block policy with full buffer).
*)
BlockStep ==
  /\ ~BufNotFull
  /\ OverflowPolicy = "block"
  /\ UNCHANGED << inQ, buf, outQ, t0 >>
  /\ cnt' = [cnt EXCEPT !.blocked_steps = @ + 1]

(*
  NoOp: stuttering step allowed by TLC (helps when neither Ingest nor EmitMin is chosen).
*)
NoOp ==
  /\ UNCHANGED << inQ, buf, outQ, t0, cnt >>

Next ==
  \/ Ingest
  \/ EmitMin
  \/ BlockStep
  \/ NoOp

(***************************************************************************)
(* Invariants                                                              *)
(***************************************************************************)

(*
  CanonicalOrderInv: outQ is canonically non-decreasing
*)
CanonicalOrderInv ==
  CanonicalNonDecreasing(outQ)

(*
  BufferPolicyInv: buffer does not exceed MaxBuf; counters are consistent with policy.
*)
BufferPolicyInv ==
  /\ Len(buf) \le MaxBuf
  /\ OverflowPolicy \in {"drop_head","drop_tail","block"}
  /\ cnt.produced \in Nat /\ cnt.dropped_head \in Nat /\ cnt.dropped_tail \in Nat /\ cnt.blocked_steps \in Nat

(*
  StableSrcInv: all events in outQ and buf have sources from allowed set; ingestion order monotone non-decreasing per source.
*)
PerSourceIngMonotone(s) ==
  LET seq == [ i \in 1..Len(outQ) : Src(outQ[i]) = s ] IN
    \A i \in 1..Max(0, Len(seq)-1) : Ing(outQ[seq[i]]) \le Ing(outQ[seq[i+1]])

StableSrcInv ==
  /\ \A e \in SetToSeq(SeqToSet(outQ)) : Src(e) \in Sources
  /\ \A e \in SetToSeq(SeqToSet(buf))  : Src(e) \in Sources
  /\ \A s \in Sources : PerSourceIngMonotone(s)

(*
  SafetyInv: composition of all SAL invariants for ordering.
*)
SafetyInv ==
  /\ CanonicalOrderInv
  /\ BufferPolicyInv
  /\ StableSrcInv

(***************************************************************************)
(* Temporal properties                                                     *)
(***************************************************************************)

(*
  Liveness (weak): if EmitMin remains enabled infinitely often and buffer is non-empty infinitely often,
  then outQ grows without violating CanonicalOrderInv. For TLC we encode as weak fairness on EmitMin.
*)
WF_Emit == WF_vars(EmitMin)

Spec == Init /\ [][Next]_<<inQ, buf, outQ, t0, cnt>>

THEOREM TypeOK ==
  Spec => [](
    /\ IsEventSeq(outQ)
    /\ IsEventSeq(buf)
    /\ cnt \in Counters
    /\ t0 \in Nat
  )

THEOREM SafetyHolds ==
  Spec => []SafetyInv

(*
  Enable weak fairness for EmitMin to avoid deadlock under perpetual ingest.
*)
FairSpec == Spec /\ WF_Emit

=============================================================================
\* End of SALOrdering.tla