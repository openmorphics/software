# Vendor Backend Development Guide (v0.1)

This guide explains how to create an out‑of‑tree vendor backend that integrates with EventFlow. It covers two integration modes, packaging with Python entry points for auto‑discovery, a minimal sample backend that initially wraps the core runtime for execution, and sample Device Capability Descriptors (DCDs) with supported ops subsets.

Authoritative references in this repo:
- Backends registry and simulators: [eventflow-backends/eventflow_backends/registry.py](eventflow-backends/eventflow_backends/registry.py), [eventflow-backends/eventflow_backends/cpu_sim/executor.py](eventflow-backends/eventflow_backends/cpu_sim/executor.py), [eventflow-backends/eventflow_backends/gpu_sim/executor.py](eventflow-backends/eventflow_backends/gpu_sim/executor.py)
- Backend API (optional compile/run_graph interface): [eventflow-backends/eventflow_backends/api.py](eventflow-backends/eventflow_backends/api.py)
- Core runtime execution helpers (for prototypes/fallbacks): [eventflow-core/eventflow_core/runtime/exec.py](eventflow-core/eventflow_core/runtime/exec.py)
- Conformance comparator (trace equivalence): [eventflow-core/eventflow_core/conformance/comparator.py](eventflow-core/eventflow_core/conformance/comparator.py)
- DCD validator and schema (see also docs/specs/*): [eventflow-core/eventflow_core/validators.py](eventflow-core/eventflow_core/validators.py)

What you will build
- A vendor backend Python package (e.g., eventflow-backends-acme) that:
  1) Registers an entry point under group “eventflow_backends” so ef CLI can auto‑discover your backend ID.
  2) Exposes a backend object with .plan(eir_dict)->plan and .run(eir_dict, inputs_jsonl, out_trace, plan=None)->run_result, OR (optionally) the minimal Backend.run_graph() interface for in‑process experiments.

Recommended integration modes

Mode A — Registry-compatible (preferred for ef CLI)
- Provide:
  - plan(eir_dict)->plan: Validate EIR vs your DCD, negotiate time mode and capabilities, emit a plan JSON (see cpu‑sim/gpu‑sim examples).
  - run(eir_dict, inputs_jsonl, out_trace, plan=None)->dict: Emit an Event Tensor JSONL trace, deterministically ordered by (ts, idx).
- Discovery: Use Python entry points (auto‑listed by ef list‑backends)

Mode B — Minimal Backend API (for embedded/prototyping)
- Provide a class implementing compile() (optional) and run_graph(g, inputs=None).
- For early bring‑up: wrap the core runtime run_event_mode() while you progressively replace nodes with device execution.
- Discovery: Not auto‑listed by ef; primarily used by in‑process scripts or the simple “mini‑registry” approach.

Entry points: Auto-discovery for ef CLI

The registry supports Python entry points under the group “eventflow_backends”. Your plugin declares a backend ID as the entry point name and points to a factory or object providing a backend instance or loader.

Example pyproject.toml for your vendor package:
```toml
[project]
name = "eventflow-backends-acme"
version = "0.1.0"
description = "Acme neuromorphic backend for EventFlow"
requires-python = ">=3.11"
dependencies = ["eventflow-core>=0.1.0", "eventflow-backends>=0.1.0"]

[project.entry-points."eventflow_backends"]
acme-asic-x1 = "acme_backend.factory:make_backend"
```

Factory module (acme_backend/factory.py):
```python
from __future__ import annotations
from .backend import AcmeBackend

def make_backend():
    # Construct and return a backend instance that implements .plan() and .run()
    return AcmeBackend()
```

Backend implementation (plan/run; registry-compatible)

A minimal skeleton that validates EIR, consults a DCD, and emits a simple plan. The run() path should write a deterministic JSONL trace. Early on, you may emulate execution like cpu‑sim (merge inputs by canonical order) and later replace with device execution.

acme_backend/backend.py:
```python
from __future__ import annotations
import json, os
from typing import Any, Dict, List, Optional, Tuple

class AcmeBackend:
    def __init__(self) -> None:
        # Load your DCD (JSON file shipped in your package)
        import importlib.resources as ir
        with ir.files("acme_backend").joinpath("dcd.json").open("r", encoding="utf-8") as f:
            self._dcd: Dict[str, Any] = json.load(f)
        # Optionally import EventFlow validators lazily
        from eventflow_core import __file__ as _  # ensure installed
        # Your backend ID
        self._name = "acme-asic-x1"

    def name(self) -> str:
        return self._name

    def dcd(self) -> Dict[str, Any]:
        return dict(self._dcd)

    def plan(self, eir: Dict[str, Any]) -> Dict[str, Any]:
        # Validate minimal EIR invariants (profile/time) and negotiate
        time_cfg = eir.get("time", {}) or {}
        mode = time_cfg.get("mode", "exact_event")
        eps_time_us = time_cfg.get("epsilon_time_us", 100)
        # Check device deterministic modes
        deterministic_modes = set(self._dcd.get("deterministic_modes", []) or [])
        time_resolution_ns = int(self._dcd.get("time_resolution_ns", 1000))
        res_us = time_resolution_ns / 1000.0
        worst_case = res_us / 2.0
        if mode == "exact_event":
            if worst_case > eps_time_us:
                raise ValueError("backend.time_quantization_violation: exact_event epsilon not met")
        elif mode == "fixed_step":
            dt_us_req = time_cfg.get("fixed_step_dt_us")
            if not isinstance(dt_us_req, int) or dt_us_req < 1:
                raise ValueError("backend.time_config_invalid: fixed_step requires positive fixed_step_dt_us")
            q = round(dt_us_req / res_us) if res_us > 0 else dt_us_req
            dt_us_sel = max(1, q) * res_us
            if abs(dt_us_sel - dt_us_req) > eps_time_us:
                raise ValueError("backend.time_quantization_violation: fixed_step dt cannot meet epsilon")
        else:
            # Optional: other modes
            pass

        return {
            "backend": {"name": self._name, "version": self._dcd.get("version", "0.1.0"), "mode": mode},
            "graph": {"id": eir.get("graph", {}).get("name", "graph"), "profile": eir.get("profile"), "seed": eir.get("seed", 0)},
            "schedule": [{"partition_id": "p0", "policy": ("fixed" if mode == "fixed_step" else "event"), "dt_us": time_cfg.get("fixed_step_dt_us")}],
            "epsilons": {"time_us": eps_time_us, "numeric": time_cfg.get("epsilon_numeric", 1e-5)},
            "negotiation": {"time": {"eir_unit": time_cfg.get("unit", "us"), "device_resolution_ns": time_resolution_ns}},
            "capabilities": {"supported_ops": sorted(self._dcd.get("supported_ops", []))},
            "notes": "acme backend plan (v0.1)",
        }

    def run(self, eir: Dict[str, Any], inputs: List[str], out_trace_path: str, plan: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Merge input event JSONL files by canonical ordering (ts, idx) as a baseline.
        # Replace this with actual device execution and trace capture when ready.
        def key(rec: Tuple[int, List[int], float]): return (rec[0], tuple(rec[1] or []))
        records: List[Tuple[int, List[int], float]] = []
        dims: List[str] = []
        units_value = "dimensionless"
        header_loaded = False
        for path in inputs:
            with open(path, "r", encoding="utf-8") as f:
                line0 = f.readline()
                if not line0:
                    continue
                header_obj = json.loads(line0)
                header = header_obj.get("header", {})
                if not header_loaded:
                    dims = header.get("dims", []) or ["ch"]
                    units = header.get("units", {})
                    units_value = units.get("value", "dimensionless")
                    header_loaded = True
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    ts = int(rec["ts"])
                    idx = list(rec.get("idx", []))
                    val = float(rec.get("val", 0.0))
                    records.append((ts, idx, val))
        records.sort(key=key)
        os.makedirs(os.path.dirname(out_trace_path) or ".", exist_ok=True)
        with open(out_trace_path, "w", encoding="utf-8") as out:
            header = {
                "schema_version": "0.1.0",
                "dims": dims or ["ch"],
                "units": {"time": "us", "value": units_value},
                "dtype": "f32",
                "layout": "coo",
                "metadata": {"backend": self._name, "plan_mode": (plan or {}).get("backend", {}).get("mode")},
            }
            out.write(json.dumps({"header": header}) + "\n")
            for ts, idx, val in records:
                out.write(json.dumps({"ts": ts, "idx": idx, "val": float(val)}) + "\n")
        return {"status": "ok", "trace_path": out_trace_path, "count": len(records)}
```

Minimal Backend API (run_graph) wrapper using run_event_mode()

You can also publish a minimal class that satisfies the abstract Backend interface for experiments. This mode is not auto‑discovered by ef registry but is useful for tests and embedded usage.

acme_backend/minimal_backend.py:
```python
from __future__ import annotations
from typing import Dict, Any, Optional
from eventflow_backends.eventflow_backends.api import Backend, DeviceCapabilityDescriptor

class MinimalBackend(Backend):
    def __init__(self):
        self.id = "acme-minimal"
        self.dcd = DeviceCapabilityDescriptor(
            name="Acme Minimal", vendor="Acme", profiles=["BASE"], time_resolution_ns=1000
        )

    def compile(self, g, constraints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {"image": None, "notes": "interpreted (prototype)"}

    def run_graph(self, g, inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Prototype execution: wrap core runtime exact-event mode
        from eventflow_core.runtime.exec import run_event_mode
        return run_event_mode(g, inputs or {})
```

Device Capability Descriptor (DCD) sample (vendor)

Create a dcd.json in your package (e.g., acme_backend/dcd.json). This should match the DCD schema documented in docs/specs and validated by EventFlow validators.

Example (fixed‑step deterministic only; two supported ops):
```json
{
  "name": "acme-asic-x1",
  "vendor": "Acme",
  "family": "XSeries",
  "version": "0.1.0",
  "time_resolution_ns": 2000,
  "max_jitter_ns": 500,
  "deterministic_modes": ["fixed_step"],
  "supported_ops": ["lif", "synapse_exp"],
  "opset_versions": { "lif": "1.0.0", "synapse_exp": "1.0.0" },
  "neuron_models": ["LIF"],
  "plasticity_rules": [],
  "weight_precisions_bits": [8, 16],
  "state_precisions_bits": [16, 32],
  "clock": { "drift_ppm": 10, "sync_method": "host_sync", "deterministic_fixed_step_only": true },
  "limits": { "max_neurons": 500000, "max_synapses": 10000000, "max_fanout": 8192, "max_fanin": 8192, "min_delay_us": 1, "max_delay_us": 100000 },
  "memory": { "per_core_kib": 131072, "per_chip_mib": 2048, "global_mib": 2048 },
  "topology": { "multi_chip": true, "cores_per_chip": 64, "max_hops": 8, "router_bandwidth_meps": 800, "link_latency_us": 3 },
  "power": { "mw_per_spike_typ": 0.05, "idle_mw": 100, "tdp_mw": 5000 },
  "features": { "on_chip_learning": false, "stochastic_neurons": false, "analog_dynamics": false, "kernel_sandbox": true },
  "overflow_behavior": "drop_tail",
  "conformance_profiles": ["BASE"],
  "notes": "Sample DCD for a fixed-step deterministic device."
}
```

Supported ops subset examples

Start with a conservative subset and extend over time:

- Minimal (spiking only):
```json
["lif", "synapse_exp", "delay_line", "probe_spike"]
```

- Vision‑centric events:
```json
["lif", "synapse_exp", "conv2d_events", "window_reduce_events", "threshold_events", "probe_spike"]
```

- Audio‑centric events:
```json
["lif", "synapse_exp", "conv1d_events", "window_reduce_events", "threshold_events", "probe_spike"]
```

Testing and validation

- Build and install your plugin in a venv:
  - pip install -e ./eventflow-core ./eventflow-backends ./eventflow-cli
  - pip install -e ./eventflow-backends-acme
- Confirm discovery (ef uses entry points to list vendor backends):
  - ef --json list-backends
- Plan with your backend:
  - ef build --eir examples/vision_optical_flow/eir.json --backend acme-asic-x1 --plan-out /tmp/acme.plan.json
- Run and produce a trace:
  - ef run --eir examples/vision_optical_flow/eir.json --backend acme-asic-x1 --input examples/vision_optical_flow/traces/inputs/vision_sample.jsonl --trace-out /tmp/acme.trace.jsonl
- Compare against a golden:
  - ef compare-traces --golden examples/vision_optical_flow/traces/golden/vision.golden.jsonl --candidate /tmp/acme.trace.jsonl

Determinism and trace conformance

- EventFlow conformance compares traces record‑by‑record under epsilon bounds.
- Emit canonical ordering (ts, idx) and consistent units (header time “us”).
- Keep run output reproducible (seed any randomness; avoid clock jitter in emitted timestamps unless device time quantization is part of DCD).

Troubleshooting

- ef list-backends does not show your backend:
  - Check entry points are installed in the active environment; run python -c "import importlib.metadata as m; print([ep.name for ep in m.entry_points().select(group='eventflow_backends')])"
  - Verify pyproject.toml [project.entry-points."eventflow_backends"] is correct.
- ef build fails due to time epsilon:
  - Adjust EIR time.epsilon_time_us or DCD time_resolution_ns/clock constraints; for fixed_step, quantize dt to your device resolution.
- ef run writes empty/short trace:
  - Validate input JSONL with ef validate --trace --path <file>, ensure header/records format and units (microseconds).
- compare-traces mismatch:
  - Inspect dt/idx mismatches; ensure your emitted idx order and time rounding match the canonical ordering.

Roadmap to device execution

1) Start with JSONL merge (simulator‑like) to validate registry plumbing.
2) Integrate device compiler path in plan() (resource checks, partitioning, lowering to device ops).
3) Replace JSONL merge in run() with device execution and trace capture (stream device outputs into header/record JSONL).
4) Add power/latency counters to run() outputs; extend plan/run metadata for richer conformance.

Security and sandboxing

- If you provide kernel code loading, implement sandboxing and resource limits aligned to the overflow_behavior and kernel_sandbox features in your DCD. Follow the security notes in docs/SECURITY.md (forthcoming alignment).

Appendix: Reference formats

- Event Tensor JSONL header
  - schema_version: "0.1.0"
  - dims: e.g., ["x","y","polarity"] or ["band"] or ["axis"]
  - units: {"time": "us", "value": "..."}
  - dtype: "f32"
  - layout: "coo"
  - metadata: freeform
- Records
  - {"ts": <int microseconds>, "idx": [..], "val": <float>}

By following this guide, vendors can ship a plugin that the ef CLI auto-discovers and that progressively moves from simulator‑style merges to full device execution while retaining deterministic semantics and conformance to the EventFlow runtime.