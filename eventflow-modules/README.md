# EventFlow Modules

`eventflow-modules` contains reference domain modules and templates built on `eventflow-core` EIR graphs. The package is useful for examples, deterministic graph construction, and test fixtures. It is not a production algorithm library.

## Current State

- Working today: many modules build typed EIR graphs and run through the core runtime in tests.
- Optional native kernels exist for selected module operations, but they require local `maturin` builds before native speedups can be validated.
- Many modules are proxies or scaffolds. They demonstrate graph patterns more than complete domain algorithms.
- Test depth is mostly smoke/end-to-end behavior, shape checks, and selected parity/performance gates. There are few golden-trace or accuracy-oriented tests.

See `docs/modules1.md` for a deeper audit of module completeness and gaps.

## Module Inventory

- Audio: STFT/mel frontends, VAD proxy, keyword-spotting proxy, diarization/localization scaffolds, always-on audio demo utilities.
- Vision: optical flow proxies, dense optical-flow work, corner tracking, object tracking, gesture-detection scaffolds.
- Robotics: SLAM/reflex/obstacle graph scaffolds.
- Time series: anomaly, change-point, and spike-mining proxies.
- Bio signals and wellness: ECG/EEG/EMG and HRV/stress/sleep scaffolds with limited physiological modeling.
- Industrial, smart agriculture, smart cities, environmental, security, autonomous vehicles, scientific research, tactile, multimodal fusion, and creative modules: broad coverage, uneven depth, mostly deterministic reference components.

## What Not To Assume

- Do not assume a module name means a finished algorithm. Several functions are minimal EIR graph proxies.
- Do not assume source arguments are fully consumed; many graphs expect runtime wiring through the CLI/runtime.
- Do not assume real sensor/device integration; SAL integration is generally through normalized Event Tensor JSONL.
- Do not claim model accuracy, regulatory readiness, or production performance without adding domain-specific validation.

## Native Acceleration

Build the optional native extension locally before running native parity or speedup gates:

```bash
python -m pip install -U maturin
(cd eventflow-modules && python -m maturin develop -r)
```

Run module native gates:

```bash
EF_NATIVE=1 EF_BENCH_GATE=1 MOD_PASS_MIN=1.3 MOD_FUSE_MIN=1.5 \
  python -m pytest -q eventflow-modules/tests/test_bench_gate_speedups.py
```

## Testing

```bash
python -m pytest -q eventflow-modules/tests -rs
python -m pytest -q tests/unit/test_modules_risk_paths.py -rs
```
