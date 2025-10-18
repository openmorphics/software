# EventFlow Domain Modules


## Native vision stub and EF_NATIVE

This package provides an optional Rust-backed vision stub for early acceleration experiments:
- Loader module: eventflow_modules._rust (exposes `native` when available)
- Native module name: eventflow_modules._rust._vision_native
- Current kernel: optical_flow_stub(frames: np.ndarray[f32, HxW]) → np.ndarray[f32, HxW] (copy placeholder)

EF_NATIVE toggle behavior follows eventflow-core:
- EF_NATIVE=1 → force native if available; warn and fall back if import fails
- EF_NATIVE=0 → force pure Python
- Unset → auto; use native when available

Quick check:
- from eventflow_modules._rust import native as vis_native
- print(getattr(vis_native, "RUST_ENABLED", False))

## Installation and local build

- pip install eventflow-modules  (installs eventflow-core dependency)
- Local dev build:
  - python -m pip install -U maturin
  - cd eventflow-modules
  - python -m maturin develop -r

Supported wheels target Python 3.8–3.12 with abi3 across macOS universal2, manylinux_2_28/musllinux, and Windows MSVC.

## Macro-benchmark example

- python -m pip install -U pytest pytest-benchmark numpy
- pytest -q eventflow-modules/tests/test_bench_optical_flow.py -k bench --benchmark-only --benchmark-autosave

CI captures autosaved results from .benchmarks and uploads artifacts (see bench.yml in the repo).

## Roadmap note

The real optical flow kernel is in progress; optical_flow_stub is a drop-in shape/ABI placeholder to enable data plumbing and benchmarking.

---

## Always-on Audio (VAD + KWS)

This package now includes an always-on audio demonstration module with a shared event-driven frontend (STFT → Mel) and dual heads:
- VAD: Event coincidence over Mel bands
- KWS: LIF neuron integration over Mel features

Core builder and runners:
- [build_always_on_graph()](eventflow-modules/eventflow_modules/audio/always_on.py:77)
- [run_wav_file()](eventflow-modules/eventflow_modules/audio/always_on.py:567)
- [run_mic_live()](eventflow-modules/eventflow_modules/audio/always_on.py:595)
- SAL/bands variants:
  - [build_always_on_bands_graph()](eventflow-modules/eventflow_modules/audio/always_on.py:715)
  - [run_wav_bands_sal()](eventflow-modules/eventflow_modules/audio/always_on.py:777)
  - [run_mic_bands_sal()](eventflow-modules/eventflow_modules/audio/always_on.py:805)

CLI entrypoint (added in [pyproject.toml](eventflow-modules/pyproject.toml:36)):
- ef-audio-demo file --path examples/wakeword/audio.wav --viz plotly --energy both
- ef-audio-demo mic --duration 15 --viz mpl --energy arm

Examples:
- Offline WAV demo: [examples/always_on_audio/file_demo.py](examples/always_on_audio/file_demo.py)
- Microphone demo: [examples/always_on_audio/mic_demo.py](examples/always_on_audio/mic_demo.py)

Optional dependencies (install as extras):
- pip install -e ./eventflow-modules[audio-viz]
  - Installs matplotlib, plotly, sounddevice

Notes:
- Microphone capture uses sounddevice (optional); if unavailable, use file mode or SAL band sources.
- Energy modeling provides ARM MCU vs Laptop CPU comparisons (heuristic constants; calibrate for hardware).
- Visualization falls back to Matplotlib if Plotly is not available.

Programmatic usage:
- Python API examples:
  - Build and run WAV:
    - from eventflow_modules.audio.always_on import build_always_on_graph, run_wav_file
    - g = build_always_on_graph()
    - result = run_wav_file("examples/wakeword/audio.wav", viz="none", energy_models="both")
  - Build bands graph and run SAL WAV bands:
    - from eventflow_modules.audio.always_on import build_always_on_bands_graph, run_wav_bands_sal
    - result = run_wav_bands_sal("examples/wakeword/audio.wav", viz="none")

Bench harness:
- A benchmarking utility will be available under examples/always_on_audio/bench.py to sweep n_fft, hop, and n_mels across energy models and write CSV/JSON outputs.

---

## Parameter validation and error policy

- Vision modules raise [VisionError](eventflow-modules/eventflow_modules/errors.py:18) for invalid parameters.
- Other domain modules raise ValueError.
- Many builders treat the first positional "source" argument as a SAL binding; you connect event iterators to specific node ids at run time.

## Vision: Gesture detection usage

- Builder: [gesture_detect()](eventflow-modules/eventflow_modules/vision/gesture_detect.py:5)

Example:
```python
from eventflow_modules.vision import gesture_detect
from eventflow_core.runtime.exec import run_event_mode

def impulses(ts_list):
    for t in ts_list:
        yield (t, 0, 1.0, {"unit": "evt"})

g = gesture_detect(None, window="5 ms", min_events=2)
out = run_event_mode(g, {"id": impulses([0, 1_000_000])})
# out["gesture"] contains coincidence events when conditions are met
```

## Robotics and Wellness updates

- Reflex controller now validates inputs and has a smoke test; see [reflex_controller()](eventflow-modules/eventflow_modules/robotics/reflex.py:5).
- Obstacle avoidance validates (window, min_count) and includes a smoke test; see [obstacle_avoidance()](eventflow-modules/eventflow_modules/robotics/obstacle.py:6).
- HRV v1 proxy implemented via Delay+Fuse; see [hrv_index()](eventflow-modules/eventflow_modules/wellness/hrv.py:5).

## Always-on Audio testing guidance

- Programmatic smoke test runs [build_always_on_graph()](eventflow-modules/eventflow_modules/audio/always_on.py:77) and [run_instrumented_event_mode()](eventflow-modules/eventflow_modules/audio/always_on.py:251) on a synthetic sine source; see [tests/test_audio_modules.py](eventflow-modules/tests/test_audio_modules.py:50).
- CLI smoke test: ef-audio-demo file --path examples/wakeword/audio.wav --viz none --energy arm; see [main()](eventflow-modules/eventflow_modules/audio/always_on.py:649).
