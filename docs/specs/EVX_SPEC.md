# EventFlow RISC-V Event eXtensions (EVX) — Specification Draft v0.1

Status: Draft  
Scope: Architectural specification for a RISC‑V simulation backend’s event-driven extension (EVX) including CSR map in 0x7C0..0x7FF range, MMIO layout, and watermark semantics compatible with EventFlow runtime determinism and SAL synchronization.

Normative language: “MUST”, “SHOULD”, “MAY” are to be interpreted as in RFC 2119.

References
- Determinism principles: [DETERMINISM.md](../DETERMINISM.md:1)
- Event Tensor schema (JSONL): [event_tensor.schema.md](eventflow-core/docs/specs/event_tensor.schema.md:1) or [event_tensor.schema.md](docs/specs/event_tensor.schema.md:1)
- EIR schema: [eir.schema.md](docs/specs/eir.schema.md:1)
- SAL watermarks: [eventflow_sal.sync.watermark](../../eventflow-sal/eventflow_sal/sync/watermark.py:1)
- Conformance comparator: [compare_traces_jsonl()](../../eventflow-core/conformance/comparator.py:1)
- Runtime exact-event executor: [run_event_mode()](../../eventflow-core/eventflow_core/runtime/exec.py:7)

1. Overview and goals

EVX defines a minimal, deterministic, event-driven extension for RISC‑V based neuromorphic workloads. It provides:
- CSR space for configuration/control and introspection (0x7C0..0x7FF).
- MMIO rings for input (host→device) and output (device→host) Event Tensor streams with explicit low/high watermarks.
- Watermark semantics for deterministic flush/fence, latency measurement, and replay boundaries aligned with SAL watermarks.
- Deterministic execution contracts: canonical ordering by (timestamp, index), epsilon-bounded time quantization, seeded pseudo-random behavior for reproducibility, and bit-exact replay.

EVX is ISA-agnostic and applies to RV32I/RV64I cores; CSR width and access atomicity follow XLEN. Counters are 64-bit via lo/hi pairs on RV32.

2. Architectural model

- Event engine: A micro-engine that ingests Event Tensor records from an IN ring, executes the current EIR program (compiled/lowered), and emits Event Tensor records to an OUT ring.
- Timestamps: Units are microseconds (us) by default; devices MAY support “cycles” or “ns” with explicit configuration.
- Processing order: Within a configurable reorder window (EVX_REORDER_US), the engine may buffer to enforce canonical ordering. Outside that window, the device MUST NOT reorder and MUST signal error on illegal reordering if enabled.
- Determinism: Any stochastic kernels MUST be seeded via EVX_SEED to ensure replay equivalence.

3. CSR map (0x7C0..0x7FF)

All CSRs are 32-bit in RV32 and 64-bit in RV64. Fields that exceed XLEN use lo/hi pairs with the “_LO/_HI” naming. W1C = write-one-to-clear.

0x7C0 EVX_VERSION [ro]
- 31:24 MAJOR, 23:16 MINOR, 15:0 PATCH
- Reset: implementation-defined, e.g., 0x01_00_00

0x7C1 EVX_CAP [ro]
- Bit 0: EXACT_EVENT mode supported
- Bit 1: FIXED_STEP mode supported
- Bit 2: WFI_WAKE supported (wfi resume on EVX IRQ)
- Bit 3: MMIO_RINGS supported
- Bit 4: IRQ supported
- Bit 5: DETERMINISTIC_CONFORMANCE (canonical (ts,idx), seeded)
- Bit 6: RVV_EVENT_OPS (vectorized event ops)
- Bit 7: HW_TIMESTAMP source available
- Bits 15:8 reserved
- Bits 23:16 MAX_DIMS (max COO dims, e.g., 4)
- Bits 31:24 RECORD_SIZE_32B_MULT (e.g., 1 → 32B records)

0x7C2 EVX_STATUS [ro]
- Bit 0: ENABLED (engine active)
- Bit 1: LIVE (rings configured and running)
- Bit 2: BACKPRESSURE (IN ring ≥ HWM)
- Bit 3: IN_UNDERRUN
- Bit 4: OUT_OVERRUN
- Bit 5: ERROR_LATCH
- Bit 6: IRQ_PENDING
- Bit 7: WM_PENDING (pending watermark completion)
- Bits 15:8 reserved
- Bits 31:16 STATE_CODE (implementation-defined microstate)

0x7C3 EVX_CTRL [rw]
- Bit 0: ENABLE (1=run, 0=halt)
- Bit 1: PAUSE (debug pause; preserves internal state)
- Bit 2: SOFT_RESET (self-clearing)
- Bit 3: FLUSH_IN (drain IN ring; self-clearing)
- Bit 4: FLUSH_OUT (flush write buffers; self-clearing)
- Bit 5: CLR_STATS (clear counters; self-clearing)
- Bit 6: IRQ_EN
- Bit 7: WM_FENCE_EN (watermark acts as fence)
- Bits 31:8 reserved

0x7C4 EVX_TIMECFG0 [rw]
- Bits 15:0 DT_US (fixed-step dt in microseconds; 0 → unused in exact_event)
- Bits 31:16 EPS_TIME_US (epsilon bound for time quantization)

0x7C5 EVX_TIMECFG1 [rw]
- Bits 1:0 TIME_UNIT (0=us, 1=ns, 2=cycles)
- Bits 7:2 reserved
- Bit 8 DET_MODE (0=best-effort deterministic, 1=strict deterministic with extra checks)
- Bits 31:9 reserved

0x7C6 EVX_SEED_LO [rw] (random seed lo)
0x7C7 EVX_SEED_HI [rw] (random seed hi)

0x7C8 EVX_IN_WM [rw]
- Bits 15:0 LWM_ENTRIES (low watermark, entries)
- Bits 31:16 HWM_ENTRIES (high watermark, entries)

0x7C9 EVX_OUT_WM [rw]
- Bits 15:0 LWM_ENTRIES
- Bits 31:16 HWM_ENTRIES

0x7CA EVX_IRQ_EN [rw]
- Bit 0: IN_LWM
- Bit 1: IN_HWM
- Bit 2: OUT_LWM
- Bit 3: OUT_HWM
- Bit 4: IN_UNDERRUN
- Bit 5: OUT_OVERRUN
- Bit 6: WM_COMPLETE
- Bit 7: ERR
- Bits 31:8 reserved

0x7CB EVX_IRQ_STATUS [rw, W1C]
- Same bit layout as EVX_IRQ_EN

0x7CC EVX_IN_COUNT_LO [ro]
0x7CD EVX_IN_COUNT_HI [ro]  (64-bit total ingested records)
0x7CE EVX_OUT_COUNT_LO [ro]
0x7CF EVX_OUT_COUNT_HI [ro] (64-bit total emitted records)

0x7D0 EVX_DROP_COUNT_LO [ro]
0x7D1 EVX_DROP_COUNT_HI [ro] (64-bit dropped records, any reason)

0x7D2 EVX_LAST_ERR [ro]
- Encoded last error: 0=noerr, 1=bad_record, 2=ts_regress, 3=overflow, 4=underrun, 5=fmt_mismatch, 6=epsilon_violation, etc.

0x7D3 EVX_LAST_ERR_INFO [ro]
- Implementation-defined aux info (e.g., offending record type or idx)

0x7D4 EVX_FMT [rw]
- Bits 3:0 DIMS (1..MAX_DIMS)
- Bits 7:4 VALUE_FMT (0=fp32, 1=fp16, 2=q15, 3=q7.8)
- Bits 15:8 IDX_BITS (per-index width; typical 16)
- Bits 23:16 RECORD_32B_MULT (1 => 32B)
- Bits 31:24 reserved

0x7D5 EVX_REORDER_US [rw]
- Reorder window in microseconds. 0 disables reordering/buffering.

0x7D6 EVX_OVERFLOW_POLICY [rw]
- 0=none (drop), 1=drop_tail, 2=drop_head, 3=stall_host, 4=backpressure_irq

0x7D7 EVX_POLICIES [rw]
- Bit 0: ENFORCE_CANONICAL_IDX_ORDER
- Bit 1: STRICT_HEADER_MATCH (input header lock)
- Bit 2: PROPAGATE_WATERMARKS (IN→OUT)
- Bits 31:3 reserved

0x7DF EVX_SCRATCH [rw]
- Freeform scratch register for driver

Reserved: 0x7E0..0x7FF for future EVX versions.

4. MMIO layout

EVX exposes a memory-mapped register file and dual SPSC rings (IN, OUT). Base addresses are device-configured (e.g., via device tree). Default simulation layout (suggested):

- EVX_CTRL region (64 KiB): base EVX_CTRL_BASE (e.g., 0xF000_0000)
- EVX_IN ring region (256 KiB): base EVX_IN_BASE (e.g., 0xF100_0000)
- EVX_OUT ring region (256 KiB): base EVX_OUT_BASE (e.g., 0xF200_0000)

4.1 Control register file (MMIO offsets from EVX_CTRL_BASE)
- 0x0000: ID/VER (ro) — mirrors EVX_VERSION
- 0x0008: CAP (ro) — mirrors EVX_CAP
- 0x0010: IN_BASE (rw, 64-bit phys)
- 0x0018: IN_SIZE (rw, bytes, power-of-two, ≥ 4096)
- 0x0020: IN_HEAD (ro, byte offset)
- 0x0028: IN_TAIL (rw, byte offset; host producer updates)
- 0x0030: IN_LWM (rw, entries)
- 0x0038: IN_HWM (rw, entries)
- 0x0040: OUT_BASE (rw, 64-bit phys)
- 0x0048: OUT_SIZE (rw, bytes, power-of-two, ≥ 4096)
- 0x0050: OUT_HEAD (rw, byte offset; host consumer updates)
- 0x0058: OUT_TAIL (ro, byte offset)
- 0x0060: OUT_LWM (rw, entries)
- 0x0068: OUT_HWM (rw, entries)
- 0x0070: DOORBELL (wo; write any value to notify device of new IN data)
- 0x0078: IRQ_EN (rw; mirrors EVX_IRQ_EN)
- 0x0080: IRQ_STATUS (rw, W1C; mirrors EVX_IRQ_STATUS)
- 0x0088: OVERFLOW_POLICY (rw; mirrors EVX_OVERFLOW_POLICY)
- 0x0090: TIMECFG0 (rw; mirrors EVX_TIMECFG0)
- 0x0098: TIMECFG1 (rw; mirrors EVX_TIMECFG1)
- 0x00A0: SEED_LO (rw)
- 0x00A8: SEED_HI (rw)
- 0x00B0: REORDER_US (rw)
- 0x00B8: FMT (rw)
- 0x00C0: CTRL (rw; mirrors EVX_CTRL)
- 0x00C8: STATUS (ro; mirrors EVX_STATUS)
- 0x00D0: IN_COUNT_LO (ro)
- 0x00D8: IN_COUNT_HI (ro)
- 0x00E0: OUT_COUNT_LO (ro)
- 0x00E8: OUT_COUNT_HI (ro)
- 0x00F0: DROP_COUNT_LO (ro)
- 0x00F8: DROP_COUNT_HI (ro)

4.2 Ring buffer format

Each ring is a circular buffer of fixed-size records. EVX v0.1 defines EVR32 records with 32-byte alignment for efficient DMA.

EVR32 (32 bytes)
- 0x00..0x07: TS (uint64, microseconds; or cycles if TIME_UNIT=cycles)
- 0x08..0x0B: IDX0 (int32)
- 0x0C..0x0F: IDX1 (int32)
- 0x10..0x13: IDX2 (int32)
- 0x14..0x17: VAL (IEEE-754 float32)
- 0x18: TYPE (uint8; 0=EVENT, 1=WATERMARK, 2=NOP, 3=HEADER_MARK)
- 0x19: NDIMS (uint8; number of valid IDX*, 0..3)
- 0x1A: FLAGS (uint8; bit0=POL, bit1=FENCE, bit2=EOS, bit7=RESERVED)
- 0x1B: RSV (uint8)
- 0x1C..0x1F: RSV (uint32)

Notes:
- For NDIMS<3, unused IDX fields MUST be zero.
- If VALUE_FMT ≠ fp32, values are mapped by driver/HW and VAL holds appropriately encoded data or a converted fp32 proxy if configured.

5. Watermark semantics

5.1 Input watermarks (host→EVX)
- A watermark is an EVR32 record with TYPE=WATERMARK and NDIMS=0, VAL=0. TS is the boundary time T.
- If EVX_CTRL.WM_FENCE_EN=1 (or EVX_POLICIES.PROPAGATE_WATERMARKS=1), a watermark acts as a fence: the device MUST NOT emit an output watermark for TS=T until it has processed all input events with TS ≤ T and drained any dependent outputs.
- Upon ingesting a watermark, the device sets EVX_STATUS.WM_PENDING=1 until completion.

5.2 Output watermarks (EVX→host)
- When the fence condition is satisfied, the device writes a corresponding watermark record to OUT with TYPE=WATERMARK and the same TS.
- If EVX_IRQ_EN.WM_COMPLETE=1, the device MUST assert an interrupt and set IRQ_STATUS.WM_COMPLETE=1 (W1C to clear).
- Output watermarks are used by SAL to align flows and by conformance tools to segment traces; see [eventflow_sal.sync.watermark](../../eventflow-sal/eventflow_sal/sync/watermark.py:1).

5.3 Backpressure and thresholds
- IN LWM/HWM semantics:
  - Crossing above IN_HWM sets STATUS.BACKPRESSURE=1 and (optionally) IRQ_STATUS.IN_HWM; overflow policy applies (stall/drop) per EVX_OVERFLOW_POLICY.
  - Dropping below IN_LWM clears BACKPRESSURE and (optionally) raises IRQ_STATUS.IN_LWM.
- OUT watermarks are primarily for host notification (OUT_LWM/HWM IRQs); OUT_HWM indicates host lag.

6. Determinism and ordering

- Canonical order: (TS ascending, IDX tuple lexicographic). If two records have identical (TS, IDX), the device MUST preserve program order or deterministic tiebreakers.
- Reordering window: Within EVX_REORDER_US, the device MAY buffer inputs to enforce canonical ordering. Inputs with TS older than now−REORDER_US MUST NOT be reordered past each other; violations set LAST_ERR=epsilon_violation or ts_regress.
- Epsilon (time): Quantization or scheduling jitter MUST remain within EPS_TIME_US. Violations MUST set an error and, depending on policy, halt or continue with a flag.
- Replay: Given the same inputs and EVX_SEED, the OUT sequence MUST be bit-equivalent (values, timestamps, IDX), enabling [compare_traces_jsonl()](../../eventflow-core/conformance/comparator.py:1) equality.

7. Initialization sequence (host)

Typical steps (abstracted):
1) Reset EVX: write EVX_CTRL.SOFT_RESET=1; poll EVX_STATUS until LIVE=0, ENABLED=0.
2) Configure format: write EVX_FMT (DIMS, VALUE_FMT, IDX_BITS, RECORD_32B_MULT).
3) Configure time: EVX_TIMECFG0(EPS_TIME_US, DT_US), EVX_TIMECFG1(TIME_UNIT, DET_MODE).
4) Configure policy: EVX_OVERFLOW_POLICY, EVX_POLICIES; set EVX_REORDER_US.
5) Seed determinism: EVX_SEED_{LO,HI}.
6) Configure rings: program IN/OUT BASE/SIZE, zero HEAD/TAIL, set IN/OUT LWM/HWM, clear IRQ_STATUS, set IRQ_EN.
7) Enable engine: EVX_CTRL.ENABLE=1 (and optionally WM_FENCE_EN, IRQ_EN).
8) Producer flow: write EVR32 records into IN at TAIL; advance TAIL; ring DOORBELL; optionally insert WATERMARK(T) to fence.
9) Consumer flow: poll OUT_TAIL vs OUT_HEAD; read output EVR32 records; advance OUT_HEAD; handle IRQs per IRQ_STATUS.

8. Interrupts

- IRQ conditions: IN_LWM, IN_HWM, OUT_LWM, OUT_HWM, IN_UNDERRUN, OUT_OVERRUN, WM_COMPLETE, ERR.
- W1C: Write a “1” to IRQ_STATUS bit to clear it. Read-modify-write recommended to avoid clearing other bits.
- WFI: If supported (EVX_CAP.WFI_WAKE), device/driver MAY use wfi to sleep until an EVX IRQ arrives.

9. Error handling

- Errors set EVX_STATUS.ERROR_LATCH and EVX_LAST_ERR/EVX_LAST_ERR_INFO.
- EVX_CTRL.SOFT_RESET clears ERROR_LATCH and counters if CLR_STATS=1 is combined.
- Drop policy: If a record must be dropped (overflow, bad format), increment EVX_DROP_COUNT and, if STRICT_HEADER_MATCH is set, optionally halt.

10. Compliance

- Header lock: When STRICT_HEADER_MATCH is enabled, device MUST reject inputs whose header units (time/value), dims, or record size do not match EVX_FMT and TIMECFG.
- Time epsilon: For TIME_UNIT=us and device resolution R (us), fixed_step dt MUST be quantized to integer multiples of R and satisfy |dt_selected − dt_requested| ≤ EPS_TIME_US.
- Conformance suite: Outgoing traces MUST pass comparator with epsilons derived from EVX_TIMECFG{0,1}. See [DETERMINISM.md](../DETERMINISM.md:1).

11. Profiles and capabilities

- EXACT_EVENT: Engine schedules on event timestamps; worst-case quantization ≤ EPS_TIME_US/2 MUST hold or a plan-time error is reported.
- FIXED_STEP: Engine buckets by DT_US; boundary emission semantics MUST match [run_event_mode()](../../eventflow-core/eventflow_core/runtime/exec.py:7) fixed-step behavior for equivalent dt.
- VECTOR EVENT OPS (RVV): When EVX_CAP.RVV_EVENT_OPS=1, implementations MAY accelerate common kernels (conv, window, threshold) while preserving determinism; this is orthogonal to EVX itself.

12. Record examples (EVR32)

Example 1 — Standard event (x,y,pol)
- TS=1_000_000 us; IDX0=x=12; IDX1=y=7; IDX2=polarity=1; VAL=1.0f; TYPE=EVENT; NDIMS=3; FLAGS=0x00.

Example 2 — Watermark fence
- TS=2_000_000 us; TYPE=WATERMARK; NDIMS=0; VAL=0; FLAGS bit1 (FENCE)=1 to request fence semantics.

13. Security and sandboxing

- Kernel sandbox: If kernels are loadable, the backend MUST adhere to policy flags (EVX_POLICIES) and the platform security guidance. Overflow policy MUST prevent unbounded ring growth or host starvation.
- Rate limiting: Ring watermarks plus OVERFLOW_POLICY SHOULD be used to enforce rate limits under untrusted sources.

14. Future extensions

- Multi-queue (priority rings) for multi-sensor fusion.
- Multi-core awareness and NUMA mapping for local rings.
- Extended record types (telemetry, perf counters) as TYPE=HEADER_MARK or TYPE=TELEMETRY.

Appendix A: Suggested default constants
- RECORD_32B_MULT=1 (EVR32=32B)
- IDX_BITS=16
- DIMS default: 3 (vision) or 1 (audio/timeseries)
- TIME_UNIT default: us
- EPS_TIME_US default: 100
- REORDER_US default: 0 (disabled)

Appendix B: Cross-component alignment
- SAL watermarks: EVX WATERMARK semantics align with SAL; see [eventflow_sal.sync.watermark](../../eventflow-sal/eventflow_sal/sync/watermark.py:1).
- Conformance: Golden/candidate comparisons use [compare_traces_jsonl()](../../eventflow-core/conformance/comparator.py:1).
- Runtime: EXACT_EVENT matches [run_event_mode()](../../eventflow-core/eventflow_core/runtime/exec.py:7) semantics (modulo time quantization and device scheduling deltas within EPS_TIME_US).