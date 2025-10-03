from __future__ import annotations

"""
Always-on audio demo (offline WAV):
- Builds the shared STFT -> Mel frontend with VAD (EventFuse) and KWS (LIF)
- Runs the instrumented pipeline on a WAV file (no specialized hardware)
- Collects per-node metrics and estimates energy for ARM MCU and Laptop CPU
- Visualizes with Plotly (default) or Matplotlib, if available

References:
- Graph builder and runner: eventflow_modules.audio.always_on
- CLI equivalent: ef-audio-demo file --path examples/wakeword/audio.wav --viz plotly --energy both

See:
- build_always_on_graph() (eventflow-modules/eventflow_modules/audio/always_on.py:87)
- run_wav_file() (eventflow-modules/eventflow_modules/audio/always_on.py:455)
"""

import argparse
import json
from typing import Any, Dict

from eventflow_modules.audio.always_on import (
    run_wav_file,
    PipelineConfig,
    FrontendConfig,
    VADConfig,
    KWSConfig,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="file_demo",
        description="Always-on audio demo (offline WAV) with energy comparison and visualization",
    )
    parser.add_argument("--path", type=str, default="examples/wakeword/audio.wav", help="Path to a WAV file (16-bit PCM)")
    parser.add_argument("--viz", type=str, choices=["mpl", "plotly", "none"], default="plotly", help="Visualization backend")
    parser.add_argument("--energy", type=str, choices=["arm", "laptop", "both"], default="both", help="Energy model(s) to compute")
    parser.add_argument("--out-json", type=str, default="", help="Optional path to write metrics/energy summary JSON")

    # Frontend + heads parameters (defaults approved)
    parser.add_argument("--sr", "--sample-rate", dest="sample_rate_hz", type=int, default=16000)
    parser.add_argument("--n_fft", type=int, default=256)
    parser.add_argument("--hop", type=str, default="10 ms")
    parser.add_argument("--n_mels", type=int, default=32)
    parser.add_argument("--fmin_hz", type=float, default=0.0)
    parser.add_argument("--fmax_hz", type=float, default=None)
    parser.add_argument("--window", type=str, default="hann")
    parser.add_argument("--mel-log", dest="mel_log", action="store_true", default=True)
    parser.add_argument("--no-mel-log", dest="mel_log", action="store_false")

    parser.add_argument("--vad-window", type=str, default="30 ms")
    parser.add_argument("--vad-min-bands", type=int, default=3)

    parser.add_argument("--kws-tau-m", type=str, default="10 ms")
    parser.add_argument("--kws-v-th", type=float, default=0.3)
    parser.add_argument("--kws-v-reset", type=float, default=0.0)
    parser.add_argument("--kws-r-m", type=float, default=1.0)
    parser.add_argument("--kws-refractory", type=str, default="2 ms")

    args = parser.parse_args(argv)

    cfg = PipelineConfig(
        fe=FrontendConfig(
            sample_rate_hz=args.sample_rate_hz,
            n_fft=args.n_fft,
            hop=args.hop,
            n_mels=args.n_mels,
            fmin_hz=args.fmin_hz,
            fmax_hz=args.fmax_hz,
            mel_log=args.mel_log,
            window=args.window,
        ),
        vad=VADConfig(
            window=args.vad_window,
            min_bands=args.vad_min_bands,
        ),
        kws=KWSConfig(
            tau_m=args.kws_tau_m,
            v_th=args.kws_v_th,
            v_reset=args.kws_v_reset,
            r_m=args.kws_r_m,
            refractory=args.kws_refractory,
        ),
    )

    result: Dict[str, Any] = run_wav_file(
        args.path,
        cfg=cfg,
        energy_models=args.energy,
        viz=args.viz,
    )

    print("=== Summary ===")
    print("mel_frames:", result.get("mel_frames"))
    per_node = result.get("per_node", {})
    for k, m in per_node.items():
        print(f"node {k}: in={m.get('in_events')} out={m.get('out_events')} time_s={m.get('wall_time_s'):.6f}")

    for e in result.get("energy", []):
        print(f"energy[{e['model']}] total_nJ={e['total_nJ']:.2f} per_node={e['per_node_nJ']}")

    if args.out_json:
        with open(args.out_json, "w") as f:
            json.dump(result, f, indent=2)
        print("Wrote JSON summary to:", args.out_json)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())