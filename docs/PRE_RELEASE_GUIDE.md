# EventFlow v0.1.0 Pre‑Release Guide

This document provides end-to-end pre-release documentation for the EventFlow multi-module Python ecosystem. It includes installation, canonical imports, inheritance/relationships, migration guidance from the stub-based layout, interdependency guidelines, code examples, troubleshooting, and packaging/API stability notes.

Modules covered:
- eventflow-core
- eventflow-sal
- eventflow-backends
- eventflow-cli
- eventflow-modules
- eventflow-hub

Version targets:
- Python >= 3.9
- Schema versions: Event Tensor JSONL 0.1.0, EIR 0.1.x

1. Installation and environment setup

Recommended: isolated virtual environment
- macOS/Linux (bash/zsh):
  - python3.11 -m venv .venv
  - source .venv/bin/activate
- Windows (PowerShell):
  - py -3.11 -m venv .venv
  - .venv\Scripts\Activate.ps1

Editable installs (preferred for development)
- pip install -e ./eventflow-core ./eventflow-sal ./eventflow-backends ./eventflow-cli ./eventflow-modules ./eventflow-hub

Alternative: repo-local PYTHONPATH for quick runs
- macOS/Linux (zsh):
  - export PYTHONPATH="eventflow-core:eventflow-sal:eventflow-backends:eventflow-cli:eventflow-modules:eventflow-hub:${PYTHONPATH:-}"
- Windows (PowerShell):
  - $env:PYTHONPATH="eventflow-core;eventflow-sal;eventflow-backends;eventflow-cli;eventflow-modules;eventflow-hub;$env:PYTHONPATH"

Quick verification
- python -c "import eventflow_core, eventflow_sal, eventflow_backends, eventflow_cli, eventflow_modules, eventflow_hub; print('OK')"

2. Canonical API import guidance

eventflow-core
- Public entry points:
  - [version()](eventflow-core/__init__.py:41)
  - [compile_and_run()](eventflow-core/__init__.py:144)
- Runtime execution helpers:
  - [run_event_mode()](eventflow-core/eventflow_core/runtime/exec.py:7)
  - [run_fixed_dt()](eventflow-core/eventflow_core/runtime/exec.py:29)
- Conformance utilities:
  - [trace_equivalent()](eventflow-core/eventflow_core/conformance/compare.py:2)
  - [compare_traces_jsonl()](eventflow-core/conformance/comparator.py:60), [print_report()](eventflow-core/conformance/comparator.py:143)
- Example imports:
  - from eventflow_core import version, compile_and_run
  - from eventflow_core.runtime.exec import run_event_mode, run_fixed_dt
  - from eventflow_core.conformance.compare import trace_equivalent

eventflow-sal
- Public entry points:
  - [stream_to_jsonl()](eventflow-sal/api.py:195)
  - [EventPacket](eventflow-sal/eventflow_sal/api/packet.py:8), [dvs_event()](eventflow-sal/eventflow_sal/api/packet.py:13), [audio_band_event()](eventflow-sal/eventflow_sal/api/packet.py:14), [imu_axis_event()](eventflow-sal/eventflow_sal/api/packet.py:15)
  - [BaseSource](eventflow-sal/eventflow_sal/api/source.py:6), [Replayable](eventflow-sal/eventflow_sal/api/source.py:32), [BaseSource.seek()](eventflow-sal/eventflow_sal/api/source.py:20)
  - [parse_sensor_uri()](eventflow-sal/eventflow_sal/api/uri.py:7), [SensorURI](eventflow-sal/eventflow_sal/api/uri.py:5)
  - [ClockModel](eventflow-sal/eventflow_sal/sync/clock.py:4), [ClockSync](eventflow-sal/eventflow_sal/sync/clock.py:10), [Watermark](eventflow-sal/eventflow_sal/sync/watermark.py:1)
  - [CalibrationStage](eventflow-sal/eventflow_sal/calib/base.py:2), [DeadPixelMask](eventflow-sal/eventflow_sal/calib/dvs.py:6), [PolarityBalance](eventflow-sal/eventflow_sal/calib/dvs.py:15)
  - Drivers: [DVSSource](eventflow-sal/eventflow_sal/drivers/dvs.py:6), [AEDAT4FileSource](eventflow-sal/eventflow_sal/drivers/dvs.py:16), [MicSource](eventflow-sal/eventflow_sal/drivers/audio.py:9), [WAVFileSource](eventflow-sal/eventflow_sal/drivers/audio.py:21), [IMUSource](eventflow-sal/eventflow_sal/drivers/imu.py:5), [CSVFileSource](eventflow-sal/eventflow_sal/drivers/imu.py:15)
- Example imports:
  - from eventflow_sal.api import stream_to_jsonl, EventPacket, dvs_event
  - from eventflow_sal.api import BaseSource, Replayable, parse_sensor_uri, SensorURI
  - from eventflow_sal.drivers import DVSSource, AEDAT4FileSource, MicSource, WAVFileSource, IMUSource, CSVFileSource
  - from eventflow_sal.sync import ClockModel, ClockSync, Watermark
  - from eventflow_sal.calib import CalibrationStage, DeadPixelMask, PolarityBalance

eventflow-backends
- Registry (authoritative):
  - [list_backends()](eventflow-backends/registry/registry.py:154), [load_backend()](eventflow-backends/registry/registry.py:158)
- Mini-registry (compatibility):
  - [get_backend()](eventflow-backends/eventflow_backends/__init__.py:20)
- CPU simulator executor:
  - [plan_cpu_sim()](eventflow-backends/cpu_sim/executor.py:44), [run_cpu_sim()](eventflow-backends/cpu_sim/executor.py:188)
- Example imports:
  - from eventflow_backends.registry.registry import list_backends, load_backend
  - from eventflow_backends import get_backend

eventflow-cli
- Console script: eventflow -> [main()](eventflow-cli/eventflow_cli/main.py:31)
- CLI subcommands:
  - SAL streaming: [cmd_sal_stream()](eventflow-cli/ef.py:265)
  - Backends: [cmd_list_backends()](eventflow-cli/ef.py:177), [cmd_build()](eventflow-cli/ef.py:505), [cmd_run()](eventflow-cli/ef.py:536)
  - Conformance: [cmd_compare_traces()](eventflow-cli/ef.py:572)

eventflow-modules
- Namespaced imports: from eventflow_modules import audio, vision, robotics, timeseries, wellness, creative
- Example: from eventflow_modules.audio import vad, kws, diarization, localization

eventflow-hub
- Hub client: [HubClient](eventflow-hub/eventflow_hub/client.py:6), [push_local()](eventflow-hub/eventflow_hub/client.py:16), [pull_local()](eventflow-hub/eventflow_hub/client.py:19)

3. Inheritance and relationships

SAL class relationships

BaseSource (abstract) -> DVSSource | MicSource | IMUSource | AEDAT4FileSource | WAVFileSource | CSVFileSource
- Emits EventPacket instances with [EventPacket](eventflow-sal/eventflow_sal/api/packet.py:8) constructors [dvs_event()](eventflow-sal/eventflow_sal/api/packet.py:13) etc.
- Optionally uses [ClockSync](eventflow-sal/eventflow_sal/sync/clock.py:10) and [Watermark](eventflow-sal/eventflow_sal/sync/watermark.py:1)

CalibrationStage (abstract) -> DeadPixelMask | PolarityBalance
- Chain stages: packets = DeadPixelMask(...).apply(packets)

Core runtime relationships

EIRGraph -> executed by [run_event_mode()](eventflow-core/eventflow_core/runtime/exec.py:7) or [run_fixed_dt()](eventflow-core/eventflow_core/runtime/exec.py:29)
Comparator: [trace_equivalent()](eventflow-core/eventflow_core/conformance/compare.py:2) (in-memory) vs [compare_traces_jsonl()](eventflow-core/conformance/comparator.py:60) (file-based)

Backends relationships

Registry: [list_backends()](eventflow-backends/registry/registry.py:154) / [load_backend()](eventflow-backends/registry/registry.py:158) -> CpuSimBackend/GpuSimBackend
CpuSimBackend -> [plan_cpu_sim()](eventflow-backends/cpu_sim/executor.py:44) -> [run_cpu_sim()](eventflow-backends/cpu_sim/executor.py:188)

4. Migration guide (from stub-based to re-exported APIs)

Summary of changes
- Removed top-level stub __init__.py in eventflow-sal/drivers/*, eventflow-sal/sync, eventflow-sal/formats
- Added explicit re-export __init__.py under eventflow_sal/api, eventflow_sal/drivers, eventflow_sal/sync, eventflow_sal/util, eventflow_sal/calib
- Removed backend stub __init__.py under eventflow-backends/gpu_sim and eventflow-backends/cpu_sim; use registry

Import mapping
- Old: from eventflow-sal/sync import ClockSync -> New: from eventflow_sal.sync import ClockSync
- Old: from eventflow-sal/drivers/dvs import DVSSource -> New: from eventflow_sal.drivers import DVSSource
- Old: from eventflow-backends/gpu_sim import ... -> New: from eventflow_backends.registry.registry import load_backend
- Old: direct open() on JSONL -> New: use [stream_to_jsonl()](eventflow-sal/api.py:195) pass-through normalization

Behavior notes
- SAL JSONL header time unit is microseconds; event timestamps emitted as microseconds in records by [_write_event()](eventflow-sal/api.py:60)
- BaseSource.seek() remains optional (raises NotImplementedError by default) in [BaseSource.seek()](eventflow-sal/eventflow_sal/api/source.py:20)

5. Module interdependencies and recommended import patterns

Dependencies (high level)
- eventflow-cli depends on eventflow-core, eventflow-sal, eventflow-backends
- eventflow-backends depends on eventflow-core validators at plan/run time
- eventflow-modules depend on eventflow-core (EIR ops/graphs) and SAL for data
- eventflow-hub is independent; optional for packaging/artifact management

Recommended patterns
- Library code should import from canonical subpackages:
  - Use eventflow_sal.* (never eventflow-sal/* file paths)
  - Use eventflow_backends.registry.registry for runtime backend selection
  - Use eventflow_core.runtime.exec helpers rather than reimplementing execution
- Keep CLI-only dynamic loaders contained within [ef.py](eventflow-cli/ef.py:39)

6. Code examples

6.1 SAL: normalize a WAV file to Event Tensor JSONL

from eventflow_sal.api import stream_to_jsonl
tele = stream_to_jsonl("audio.mic:///path/to/audio.wav", "/tmp/audio.jsonl", bands=32, hop_ms=10, telemetry_out="/tmp/audio.telemetry.json")
print(tele["count"], "events written")

6.2 Custom BaseSource

from typing import Iterator
from eventflow_sal.api import BaseSource, EventPacket

class MySource(BaseSource):
    def metadata(self): return {"kind":"custom.source"}
    def subscribe(self) -> Iterator[EventPacket]:
        for i in range(10):
            ts_ns = i * 1_000_000
            self._watermark_ns = ts_ns
            yield EventPacket(ts_ns, 0, float(i), {"unit":"custom"})

6.3 Backends: plan and run via registry

import json
from eventflow_backends.registry.registry import load_backend
from eventflow_core import version

be = load_backend("cpu-sim")
eir = {"graph":{"name":"demo"}, "time":{"mode":"exact_event","unit":"us","epsilon_time_us":100}, "nodes":[], "edges":[]}
plan = be.plan(eir)
res = be.run(eir, inputs=["/tmp/audio.jsonl"], out_trace_path="/tmp/trace.jsonl", plan=plan)
print(json.dumps({"plan": plan["backend"], "run": res["count"]}, indent=2))

6.4 Core runtime: compile_and_run convenience

from eventflow_core import compile_and_run
result = compile_and_run("examples/vision_optical_flow/eir.json", backend="cpu-sim", constraints={"inputs": ["examples/vision_optical_flow/traces/inputs/vision_sample.jsonl"], "trace_out": "/tmp/vision.trace.jsonl"})
print(result["status"], result["backend"])

6.5 Conformance: compare traces

from eventflow_core.conformance.compare import trace_equivalent
from eventflow_core.conformance import comparator  # dynamic CLI-oriented reader
ok = trace_equivalent({"a":[]},{"a":[]})
report = comparator.compare_traces_jsonl("golden.jsonl","candidate.jsonl")
print(ok, report["ok"])

7. Troubleshooting

ModuleNotFoundError for eventflow_* packages
- Ensure venv is active and either pip install -e ... was run, or PYTHONPATH includes all six module roots (see Section 1).

Unknown backend 'X'
- Verify name in [list_backends()](eventflow-backends/registry/registry.py:154). For simulators, use "cpu-sim" or "gpu-sim".

SAL JSONL “open()” errors
- JSONL normalization must use [stream_to_jsonl()](eventflow-sal/api.py:195) (registry intentionally rejects JSONL in [resolve_source()](eventflow-sal/eventflow_sal/registry.py:33)).

Time units mismatch
- SAL writes microsecond timestamps in records (see [_write_event()](eventflow-sal/api.py:60)); ensure downstream tools expect microseconds.

CLI not found
- If installed: run "eventflow". In repo-only usage: "python -u eventflow-cli/ef.py".

8. Packaging and API stability

Public/stable APIs for v0.1.0
- Core: [version()](eventflow-core/__init__.py:41), [compile_and_run()](eventflow-core/__init__.py:144), [run_event_mode()](eventflow-core/eventflow_core/runtime/exec.py:7), [run_fixed_dt()](eventflow-core/eventflow_core/runtime/exec.py:29), [trace_equivalent()](eventflow-core/eventflow_core/conformance/compare.py:2)
- SAL: [stream_to_jsonl()](eventflow-sal/api.py:195), [EventPacket](eventflow-sal/eventflow_sal/api/packet.py:8) and constructors, [BaseSource](eventflow-sal/eventflow_sal/api/source.py:6), [parse_sensor_uri()](eventflow-sal/eventflow_sal/api/uri.py:7), [ClockSync](eventflow-sal/eventflow_sal/sync/clock.py:10)
- Backends: [list_backends()](eventflow-backends/registry/registry.py:154), [load_backend()](eventflow-backends/registry/registry.py:158), [get_backend()](eventflow-backends/eventflow_backends/__init__.py:20), [plan_cpu_sim()](eventflow-backends/cpu_sim/executor.py:44), [run_cpu_sim()](eventflow-backends/cpu_sim/executor.py:188)
- CLI: [cmd_sal_stream()](eventflow-cli/ef.py:265), [cmd_build()](eventflow-cli/ef.py:505), [cmd_run()](eventflow-cli/ef.py:536), [cmd_compare_traces()](eventflow-cli/ef.py:572)
- Hub: [HubClient](eventflow-hub/eventflow_hub/client.py:6)

Semantic versioning and compatibility
- We follow SemVer. Public APIs above are covered by backward-compatibility guarantees across patch/minor releases. Experimental/internal modules (anything not listed above) may change.
- JSON schema versions (Event Tensor header, DCD, EIR) are tracked in docs/specs. When schema versions change, CLI validators will enforce compatibility.

Deprecation policy
- Deprecated imports will be maintained for one minor release where feasible. Use the Migration guide mappings to update code.

9. Appendix: CLI quick reference

ef --json version
ef --json list-backends
ef sal-stream --uri "vision.dvs://file?format=jsonl&path=examples/vision_optical_flow/traces/inputs/vision_sample.jsonl" --out /tmp/vision.norm.jsonl --telemetry-out /tmp/vision.telemetry.json
ef build --eir examples/vision_optical_flow/eir.json --backend cpu-sim --plan-out /tmp/plan.json
ef run --eir examples/vision_optical_flow/eir.json --backend cpu-sim --input examples/vision_optical_flow/traces/inputs/vision_sample.jsonl --trace-out /tmp/trace.jsonl
ef compare-traces --golden examples/vision_optical_flow/traces/golden/vision.golden.jsonl --candidate /tmp/trace.jsonl

Test matrix (repo-local)

export PYTHONPATH="eventflow-core:eventflow-sal:eventflow-backends:eventflow-cli:eventflow-modules:eventflow-hub:${PYTHONPATH:-}"
python3 -m unittest discover -s eventflow-sal/tests -v
python3 -m unittest discover -s eventflow-core/tests -v
python3 -m unittest discover -s eventflow-backends/tests -v
python3 -m unittest discover -s eventflow-cli/tests -v
python3 -m unittest discover -s eventflow-modules/tests -v

End of document.