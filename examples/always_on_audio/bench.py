from __future__ import annotations

"""
Always-on audio benchmarking harness.

Sweeps frontend parameters (n_fft, hop, n_mels) over a WAV file input and records:
- Per-node metrics (in/out counts, wall time)
- Energy estimates for selected model(s): ARM MCU, Laptop CPU, or both
- Aggregated CSV and JSON outputs for downstream analysis

Usage examples:
- python examples/always_on_audio/bench.py --path examples/wakeword/audio.wav --energy both --viz none
- Custom sweeps:
  python examples/always_on_audio/bench.py \
    --path examples/wakeword/audio.wav \
    --n_fft 64 128 256 \
    --hop "5 ms" "10 ms" \
    --n_mels 16 32 \
    --energy both \
    --viz none \
    --csv-out examples/always_on_audio/out/bench.csv \
    --json-out examples/always_on_audio/out/bench.json

References:
- run_wav_file() (eventflow-modules/eventflow_modules/audio/always_on.py:567)
"""

import argparse
import csv
import json
import os
from typing import Any, Dict, List, Tuple

from eventflow_modules.audio.always_on import (
    run_wav_file,
    PipelineConfig,
    FrontendConfig,
    VADConfig,
    KWSConfig,
)

DEFAULT_NFFT = [64, 128, 256]
DEFAULT_HOP = ["5 ms", "10 ms"]
DEFAULT_NMELS = [16, 32]

CSV_COLUMNS = [
    "wav_path",
    "n_fft",
    "hop",
    "n_mels",
    "energy_model",
    "total_nJ",
    "stft_nJ",
    "mel_nJ",
    "vad_nJ",
    "kws_nJ",
    "mel_frames",
    # Per-node metrics
    "stft_in",
    "stft_out",
    "stft_time_s",
    "mel_in",
    "mel_out",
    "mel_time_s",
    "vad_in",
    "vad_out",
    "vad_time_s",
    "kws_in",
    "kws_out",
    "kws_time_s",
]


def _extract_node(metrics: Dict[str, Any], name: str) -> Tuple[int, int, float]:
    node = metrics.get(name, {"in_events": 0, "out_events": 0, "wall_time_s": 0.0})
    return int(node.get("in_events", 0)), int(node.get("out_events", 0)), float(node.get("wall_time_s", 0.0))


def bench_once(
    wav_path: str,
    n_fft: int,
    hop: str,
    n_mels: int,
    energy: str,
    viz: str = "none",
) -> Dict[str, Any]:
    cfg = PipelineConfig(
        fe=FrontendConfig(
            sample_rate_hz=16000,
            n_fft=n_fft,
            hop=hop,
            n_mels=n_mels,
            fmin_hz=0.0,
            fmax_hz=None,
            mel_log=True,
            window="hann",
        ),
        vad=VADConfig(window="30 ms", min_bands=3),
        kws=KWSConfig(tau_m="10 ms", v_th=0.3),
    )
    result = run_wav_file(
        wav_path,
        cfg=cfg,
        energy_models=energy,
        viz=viz,
    )
    return result


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="always_on_bench",
        description="Benchmark always-on audio pipeline across parameter sweeps and energy models",
    )
    parser.add_argument("--path", type=str, default="examples/wakeword/audio.wav", help="Path to WAV file (16-bit PCM)")
    parser.add_argument("--viz", type=str, choices=["mpl", "plotly", "none"], default="none", help="Visualization backend (default none)")
    parser.add_argument("--energy", type=str, choices=["arm", "laptop", "both"], default="both", help="Energy model(s) to compute")

    parser.add_argument("--n_fft", type=int, nargs="+", default=DEFAULT_NFFT, help="List of n_fft values to sweep")
    parser.add_argument("--hop", type=str, nargs="+", default=DEFAULT_HOP, help="List of hop durations to sweep (e.g., '5 ms' '10 ms')")
    parser.add_argument("--n_mels", type=int, nargs="+", default=DEFAULT_NMELS, help="List of mel bands to sweep")

    parser.add_argument("--csv-out", type=str, default="examples/always_on_audio/out/bench.csv", help="CSV output path")
    parser.add_argument("--json-out", type=str, default="examples/always_on_audio/out/bench.json", help="JSON output path")

    args = parser.parse_args(argv)

    out_dir = os.path.dirname(args.csv_out) or "."
    os.makedirs(out_dir, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    json_records: List[Dict[str, Any]] = []

    for n_fft in args.n_fft:
        for hop in args.hop:
            for n_mels in args.n_mels:
                print(f"[bench] path={args.path} n_fft={n_fft} hop={hop} n_mels={n_mels} energy={args.energy}")
                result = bench_once(args.path, n_fft, hop, n_mels, args.energy, viz=args.viz)
                per_node = result.get("per_node", {})
                mel_frames = int(result.get("mel_frames", 0))

                stft_in, stft_out, stft_t = _extract_node(per_node, "stft")
                mel_in, mel_out, mel_t = _extract_node(per_node, "mel")
                vad_in, vad_out, vad_t = _extract_node(per_node, "vad")
                kws_in, kws_out, kws_t = _extract_node(per_node, "kws")

                # Multiple energy models may be returned
                for e in result.get("energy", []):
                    model = str(e.get("model"))
                    total_nj = float(e.get("total_nJ", 0.0))
                    per_node_nj = e.get("per_node_nJ", {})
                    row = {
                        "wav_path": args.path,
                        "n_fft": int(n_fft),
                        "hop": hop,
                        "n_mels": int(n_mels),
                        "energy_model": model,
                        "total_nJ": total_nj,
                        "stft_nJ": float(per_node_nj.get("stft", 0.0)),
                        "mel_nJ": float(per_node_nj.get("mel", 0.0)),
                        "vad_nJ": float(per_node_nj.get("vad", 0.0)),
                        "kws_nJ": float(per_node_nj.get("kws", 0.0)),
                        "mel_frames": mel_frames,
                        "stft_in": stft_in,
                        "stft_out": stft_out,
                        "stft_time_s": stft_t,
                        "mel_in": mel_in,
                        "mel_out": mel_out,
                        "mel_time_s": mel_t,
                        "vad_in": vad_in,
                        "vad_out": vad_out,
                        "vad_time_s": vad_t,
                        "kws_in": kws_in,
                        "kws_out": kws_out,
                        "kws_time_s": kws_t,
                    }
                    rows.append(row)

                json_records.append({
                    "wav_path": args.path,
                    "n_fft": int(n_fft),
                    "hop": hop,
                    "n_mels": int(n_mels),
                    "mel_frames": mel_frames,
                    "per_node": per_node,
                    "energy": result.get("energy", []),
                })

    # Write CSV
    with open(args.csv_out, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print("Wrote CSV:", args.csv_out)

    # Write JSON
    with open(args.json_out, "w") as f:
        json.dump(json_records, f, indent=2)
    print("Wrote JSON:", args.json_out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())