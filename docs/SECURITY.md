# Security and Safety Model — Specification v0.1

Objectives
- Prevent untrusted kernels from escaping process or exceeding resource budgets.
- Enforce rate limiting and overflow policies on sensor streams.
- Detect spoofing/anomalies; provide audit trails and reproducible diagnostics.

Scope
- Kernel sandboxing strategies (process isolation, seccomp, containers; TBD)
- Resource limits: CPU, memory, file I/O, network (default off for local dev)
- SAL safety checks: value ranges, index bounds, NaN/Inf filtering
- Telemetry and counters for drops, blocks, anomalies (see [docs/CONFORMANCE.md](docs/CONFORMANCE.md))

Policy precedence
1) CLI/runtime options
2) EIR.graph.security defaults (see [docs/specs/eir.schema.md](docs/specs/eir.schema.md))
3) Backend/SAL defaults

Threats considered (baseline)
- Malicious inputs attempting denial of service via rate floods or extreme values
- Timing spoofing via jitter/drift manipulation
- Kernel code attempting unauthorized IO or escaping process

Mitigations (baseline)
- Bounded buffers with explicit overflow policy
- Stable canonical ordering and timestamp normalization
- Process isolation for custom kernels; no dynamic code by default in v0.1
