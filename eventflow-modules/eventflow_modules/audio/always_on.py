from __future__ import annotations

"""
Always-on audio processing with shared frontend (STFT -> Mel) and dual heads:
- VAD (EventFuse coincidence on mel bands)
- KWS (LIF neuron integration on mel bands)

This module provides:
- Graph builder for a shared, event-driven pipeline
- Streaming utilities (WAV offline, optional microphone)
- Instrumented runner that collects per-node metrics
- Energy consumption modeling with ARM MCU and Laptop CPU profiles
- Visualization utilities (Matplotlib for CLI, Plotly for notebooks)
- CLI entrypoint: ef-audio-demo (to be added in pyproject via [project.scripts])

Inputs to the graph are PCM-like events: (t_ns, ch=0, value, {"unit":"pcm"})
Outputs are standard EventFlow operator outputs for mel, vad, kws nodes.
"""

import argparse
import math
import time
import wave
import struct
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Tuple, Optional, Iterable

# Event tuple: (timestamp_ns, channel, value, metadata)
Event = Tuple[int, int, float, dict]

# EventFlow core imports
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import STFT, MelBands, EventFuse, LIFNeuron
from eventflow_core.eir.types import time_to_ns
from eventflow_core.runtime.scheduler import build_exec_nodes


# ----------------------------
# Configuration dataclasses
# ----------------------------

@dataclass
class FrontendConfig:
    sample_rate_hz: int = 16000
    n_fft: int = 256
    hop: str = "10 ms"
    n_mels: int = 32
    fmin_hz: float = 0.0
    fmax_hz: Optional[float] = None
    mel_log: bool = True
    window: str = "hann"

@dataclass
class VADConfig:
    window: str = "30 ms"
    min_bands: int = 3

@dataclass
class KWSConfig:
    tau_m: str = "10 ms"
    v_th: float = 0.3
    v_reset: float = 0.0
    r_m: float = 1.0
    refractory: str = "2 ms"

@dataclass
class PipelineConfig:
    fe: FrontendConfig = field(default_factory=FrontendConfig)
    vad: VADConfig = field(default_factory=VADConfig)
    kws: KWSConfig = field(default_factory=KWSConfig)


# ----------------------------
# Graph builder
# ----------------------------

def build_always_on_graph(
    params: Optional[Dict[str, Any]] = None
) -> EIRGraph:
    """
    Build a shared frontend graph with VAD and KWS heads:
      stft.spec -> mel.in
      mel.mel -> vad.a
      mel.mel -> vad.b
      mel.mel -> kws.in
    """
    p = params or {}
    fe = FrontendConfig(
        sample_rate_hz=int(p.get("sample_rate_hz", 16000)),
        n_fft=int(p.get("n_fft", 256)),
        hop=p.get("hop", "10 ms"),
        n_mels=int(p.get("n_mels", 32)),
        fmin_hz=float(p.get("fmin_hz", 0.0)),
        fmax_hz=p.get("fmax_hz"),
        mel_log=bool(p.get("mel_log", True)),
        window=p.get("window", "hann"),
    )
    vadc = VADConfig(
        window=p.get("vad_window", p.get("window_vad", "30 ms")),
        min_bands=int(p.get("vad_min_bands", 3)),
    )
    kwsc = KWSConfig(
        tau_m=p.get("kws_tau_m", "10 ms"),
        v_th=float(p.get("kws_v_th", 0.3)),
        v_reset=float(p.get("kws_v_reset", 0.0)),
        r_m=float(p.get("kws_r_m", 1.0)),
        refractory=p.get("kws_refractory", "2 ms"),
    )

    g = EIRGraph()
    g.add_node(
        "stft",
        STFT(
            "stft",
            n_fft=fe.n_fft,
            hop=fe.hop,
            sample_rate_hz=fe.sample_rate_hz,
            window=fe.window,
        ).as_op(),
    )
    g.add_node(
        "mel",
        MelBands(
            "mel",
            n_fft=fe.n_fft,
            n_mels=fe.n_mels,
            sample_rate_hz=fe.sample_rate_hz,
            fmin_hz=fe.fmin_hz,
            fmax_hz=fe.fmax_hz,
            log=fe.mel_log,
        ).as_op(),
    )
    g.add_node(
        "vad",
        EventFuse(
            "vad", window=vadc.window, min_count=vadc.min_bands
        ).as_op(),
    )
    g.add_node(
        "kws",
        LIFNeuron(
            "kws",
            tau_m=kwsc.tau_m,
            v_th=kwsc.v_th,
            v_reset=kwsc.v_reset,
            r_m=kwsc.r_m,
            refractory=kwsc.refractory,
        ).as_op(),
    )

    g.connect("stft", "spec", "mel", "in")
    g.connect("mel", "mel", "vad", "a")
    g.connect("mel", "mel", "vad", "b")
    g.connect("mel", "mel", "kws", "in")
    return g


# ----------------------------
# Streaming utilities
# ----------------------------

def wav_pcm_events(path: str) -> Iterator[Event]:
    """
    Pure-Python WAV reader that yields mono PCM events normalized to [-1, 1].
    Supports 16-bit PCM. For multi-channel audio, channels are averaged.
    """
    with wave.open(path, "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        n_frames = wf.getnframes()
        if sampwidth != 2:
            raise ValueError(f"Only 16-bit PCM WAV supported, got sampwidth={sampwidth}")

        frames_remaining = n_frames
        idx = 0
        chunk = 4096

        while frames_remaining > 0:
            to_read = min(chunk, frames_remaining)
            raw = wf.readframes(to_read)
            frames_remaining -= to_read
            # convert to int16
            count = len(raw) // 2
            ints = struct.unpack("<{}h".format(count), raw)
            # average channels if needed
            if n_channels == 1:
                seq = ints
            else:
                seq = []
                for j in range(0, len(ints), n_channels):
                    acc = 0
                    for c in range(n_channels):
                        acc += ints[j + c]
                    seq.append(int(acc / n_channels))

            for s in seq:
                t_ns = int(idx * 1e9 / framerate)
                val = float(s) / 32768.0
                yield (t_ns, 0, val, {"unit": "pcm"})
                idx += 1


def mic_pcm_events(duration_s: float = 15.0, sample_rate_hz: int = 16000) -> Iterator[Event]:
    """
    Optional microphone capture using sounddevice if available.
    Captures a blocking buffer for duration_s, then emits PCM events.
    """
    try:
        import sounddevice as sd  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "sounddevice is not installed. Install it or use SAL MicSource or WAV input."
        ) from e

    n_samples = int(duration_s * sample_rate_hz)
    buf = sd.rec(n_samples, samplerate=sample_rate_hz, channels=1, dtype="float32")
    sd.wait()
    # buf: shape (n_samples, 1)
    for i in range(n_samples):
        t_ns = int(i * 1e9 / sample_rate_hz)
        yield (t_ns, 0, float(buf[i, 0]), {"unit": "pcm"})


# ----------------------------
# Instrumented runner
# ----------------------------

@dataclass
class NodeMetrics:
    kind: str
    in_events: int
    out_events: int
    wall_time_s: float

@dataclass
class RunReport:
    outputs: Dict[str, List[Event]]
    per_node: Dict[str, NodeMetrics]
    mel_frames: int
    mel_unique_times: List[int]  # sorted
    config: PipelineConfig


def _counting_iter(it: Iterator[Event], counter: List[int]) -> Iterator[Event]:
    for ev in it:
        counter[0] += 1
        yield ev


def run_instrumented_event_mode(
    g: EIRGraph,
    inputs: Dict[str, Iterator[Event]],
    config: PipelineConfig,
) -> RunReport:
    """
    Mirrors eventflow_core.runtime.exec.run_event_mode but adds per-node timing and input counts.
    """
    topo = g.topo()
    exec_nodes = build_exec_nodes(g)
    # Build sinks map
    sinks: Dict[str, List[Tuple[str, str]]] = {nid: [] for nid in g.nodes}
    for e in g.edges:
        sinks[e.src[0]].append(e.dst)

    # Upstream port map
    upstream: Dict[str, Dict[str, Iterator[Event]]] = {nid: {"in": iter([]), "pre": iter([]), "a": iter([]), "b": iter([])} for nid in g.nodes}
    for name, it in inputs.items():
        if name in upstream:
            upstream[name]["in"] = it
        else:
            upstream[name] = {"in": it}

    outputs: Dict[str, List[Event]] = {nid: [] for nid in g.nodes}
    per_node: Dict[str, NodeMetrics] = {}

    for nid in topo:
        ex = exec_nodes[nid]
        if ex.kind == "fuse":
            # two inputs a and b
            cnt_a = [0]
            cnt_b = [0]
            it_a = upstream[nid].get("a", iter([]))
            it_b = upstream[nid].get("b", iter([]))
            it_a_c = _counting_iter(it_a, cnt_a)
            it_b_c = _counting_iter(it_b, cnt_b)
            t0 = time.perf_counter()
            out_list = list(ex.fn(it_a_c, it_b_c))
            dt = time.perf_counter() - t0
            outputs[nid].extend(out_list)
            per_node[nid] = NodeMetrics(
                kind=ex.kind,
                in_events=cnt_a[0] + cnt_b[0],
                out_events=len(out_list),
                wall_time_s=dt,
            )
        else:
            # single input port "in" or "pre"
            it_in = upstream[nid].get("in", upstream[nid].get("pre", iter([])))
            cnt_in = [0]
            it_in_c = _counting_iter(it_in, cnt_in)
            t0 = time.perf_counter()
            out_list = list(ex.fn(it_in_c))
            dt = time.perf_counter() - t0
            outputs[nid].extend(out_list)
            per_node[nid] = NodeMetrics(
                kind=ex.kind,
                in_events=cnt_in[0],
                out_events=len(out_list),
                wall_time_s=dt,
            )

        # fan out to downstream ports
        for (dst_id, dport) in sinks[nid]:
            upstream[dst_id][dport] = iter(outputs[nid])

    # Derive mel frames (unique times)
    mel_times = sorted({t for (t, _, _, _) in outputs.get("mel", [])})
    return RunReport(
        outputs=outputs,
        per_node=per_node,
        mel_frames=len(mel_times),
        mel_unique_times=mel_times,
        config=config,
    )


# ----------------------------
# Energy modeling
# ----------------------------

@dataclass
class EnergyBreakdown:
    per_node_nj: Dict[str, float]
    total_nj: float
    model_name: str

class EnergyModel:
    """
    Simple parametric energy model.

    All energies are in nanojoules (nJ).
    """
    def __init__(self, name: str, e_per_mac_nj: float, e_per_op_nj: float):
        self.name = name
        self.e_per_mac_nj = e_per_mac_nj
        self.e_per_op_nj = e_per_op_nj

    def _fft_macs(self, n_fft: int) -> float:
        # Radix-2 FFT approx MACs (heuristic). Factor 5*N*log2(N)
        return 5.0 * n_fft * math.log2(max(2, n_fft))

    def estimate(
        self,
        report: RunReport,
        params: Dict[str, Any],
    ) -> EnergyBreakdown:
        n_fft = int(params.get("n_fft", 256))
        n_mels = int(params.get("n_mels", 32))
        mel_log = bool(params.get("mel_log", True))  # no-op here but documented
        frames = max(0, report.mel_frames)
        n_bins = n_fft // 2 + 1

        per_node: Dict[str, float] = {}

        # STFT: frames * fft_macs
        stft_macs = frames * self._fft_macs(n_fft)
        per_node["stft"] = stft_macs * self.e_per_mac_nj

        # Mel: frames * (n_mels * n_bins MACs)  (coarse upper bound)
        mel_macs = frames * (n_mels * n_bins)
        per_node["mel"] = mel_macs * self.e_per_mac_nj

        # VAD (fuse): per input event a few comparisons/ops
        vad_in = report.per_node.get("vad", NodeMetrics("fuse", 0, 0, 0.0)).in_events
        per_node["vad"] = vad_in * 4.0 * self.e_per_op_nj  # comparisons, heap ops (heuristic)

        # KWS (LIF): per input event small ops (+ threshold)
        kws_in = report.per_node.get("kws", NodeMetrics("lif", 0, 0, 0.0)).in_events
        per_node["kws"] = kws_in * 6.0 * self.e_per_op_nj

        total = sum(per_node.values())
        return EnergyBreakdown(per_node, total, self.name)


def compare_energy_models(
    report: RunReport,
    params: Dict[str, Any],
    which: str = "both",
) -> List[EnergyBreakdown]:
    """
    Return a list of EnergyBreakdown for the selected models.
    'arm' | 'laptop' | 'both'
    """
    # Heuristic constants (nJ per operation)
    # These are illustrative and should be calibrated with hardware measurements.
    arm = EnergyModel("ARM_MCU", e_per_mac_nj=0.03, e_per_op_nj=0.01)
    laptop = EnergyModel("LAPTOP_CPU", e_per_mac_nj=0.3, e_per_op_nj=0.05)

    models: List[EnergyModel] = []
    if which in ("arm", "both"):
        models.append(arm)
    if which in ("laptop", "both"):
        models.append(laptop)

    return [m.estimate(report, params) for m in models]


# ----------------------------
# Visualization
# ----------------------------

def _mel_matrix_from_events(mel_events: List[Event], n_mels: int) -> Tuple[List[int], List[List[float]]]:
    """
    Group mel events by time and build a [frames x n_mels] matrix.
    Returns (sorted_times, matrix)
    """
    by_time: Dict[int, List[Tuple[int, float]]] = {}
    for t, ch, val, meta in mel_events:
        by_time.setdefault(t, []).append((ch, float(val)))
    times = sorted(by_time.keys())
    mat: List[List[float]] = []
    for t in times:
        row = [0.0] * n_mels
        for ch, v in by_time[t]:
            if 0 <= ch < n_mels:
                row[ch] = v
        mat.append(row)
    return times, mat


def visualize(
    report: RunReport,
    params: Dict[str, Any],
    energy: List[EnergyBreakdown],
    backend: str = "mpl",  # "mpl" | "plotly" | "none"
) -> None:
    if backend == "none":
        return

    mel_events = report.outputs.get("mel", [])
    n_mels = int(params.get("n_mels", 32))
    sr = int(params.get("sample_rate_hz", 16000))
    times, mel_mat = _mel_matrix_from_events(mel_events, n_mels)
    times_s = [t / 1e9 for t in times]
    vad_events = report.outputs.get("vad", [])
    kws_events = report.outputs.get("kws", [])

    if backend == "plotly":
        try:
            import plotly.graph_objs as go  # type: ignore
            from plotly.subplots import make_subplots  # type: ignore
        except Exception:
            backend = "mpl"  # fallback

    if backend == "plotly":
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, row_heights=[0.7, 0.3])
        # Mel spectrogram
        fig.add_trace(
            go.Heatmap(
                z=[row for row in zip(*mel_mat)],  # transpose for mel on y-axis
                x=times_s,
                y=list(range(n_mels)),
                colorscale="Viridis",
                colorbar={"title": "Mel"},
            ),
            row=1, col=1,
        )
        # VAD and KWS timeline
        fig.add_trace(
            go.Scatter(
                x=[t / 1e9 for (t, _, _, _) in vad_events],
                y=[1.0] * len(vad_events),
                mode="markers",
                marker={"color": "orange"},
                name="VAD",
            ),
            row=2, col=1,
        )
        fig.add_trace(
            go.Scatter(
                x=[t / 1e9 for (t, _, _, _) in kws_events],
                y=[1.2] * len(kws_events),
                mode="markers",
                marker={"color": "red"},
                name="KWS",
            ),
            row=2, col=1,
        )

        # Energy bars
        for eb in energy:
            fig.add_trace(
                go.Bar(
                    x=list(eb.per_node_nj.keys()),
                    y=list(eb.per_node_nj.values()),
                    name=f"Energy ({eb.model_name}) [nJ]",
                ),
                row=2, col=1,
            )

        fig.update_layout(title="Always-on Audio: Mel + VAD + KWS + Energy", xaxis_title="Time [s]")
        fig.show()
        return

    # Matplotlib
    try:
        import matplotlib.pyplot as plt  # type: ignore
    except Exception:
        return  # no plotting available

    fig, (ax0, ax1) = plt.subplots(2, 1, figsize=(10, 6), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    # Mel heatmap
    if mel_mat:
        import numpy as np  # type: ignore
        mel_arr = np.array(mel_mat, dtype=float)  # [frames, n_mels]
        ax0.imshow(mel_arr.T, aspect="auto", origin="lower", interpolation="nearest")
        ax0.set_ylabel("Mel band")
    ax0.set_title("Mel Spectrogram")

    # VAD/KWS events and energy bars
    ax1.scatter([t / 1e9 for (t, _, _, _) in vad_events], [1.0] * len(vad_events), c="orange", s=10, label="VAD")
    ax1.scatter([t / 1e9 for (t, _, _, _) in kws_events], [1.2] * len(kws_events), c="red", s=10, label="KWS")

    # Energy: stack side-by-side bars
    if energy:
        labels = list(energy[0].per_node_nj.keys())
        x0 = 0.0
        width = 0.15
        for i, eb in enumerate(energy):
            xs = [x + i * width for x in range(len(labels))]
            ys = [eb.per_node_nj.get(k, 0.0) for k in labels]
            ax1.bar(xs, ys, width=width, label=f"Energy {eb.model_name} [nJ]")
        ax1.set_xticks([x + (len(energy) - 1) * width / 2 for x in range(len(labels))], labels, rotation=0)

    ax1.set_xlabel("Time [s]")
    ax1.legend(loc="upper right")
    plt.tight_layout()
    plt.show()


# ----------------------------
# Orchestration helpers
# ----------------------------

def _shared_params_from_config(cfg: PipelineConfig) -> Dict[str, Any]:
    fe = cfg.fe
    return {
        "sample_rate_hz": fe.sample_rate_hz,
        "n_fft": fe.n_fft,
        "hop": fe.hop,
        "n_mels": fe.n_mels,
        "fmin_hz": fe.fmin_hz,
        "fmax_hz": fe.fmax_hz,
        "mel_log": fe.mel_log,
        "window": fe.window,
        "vad_window": cfg.vad.window,
        "vad_min_bands": cfg.vad.min_bands,
        "kws_tau_m": cfg.kws.tau_m,
        "kws_v_th": cfg.kws.v_th,
        "kws_v_reset": cfg.kws.v_reset,
        "kws_r_m": cfg.kws.r_m,
        "kws_refractory": cfg.kws.refractory,
    }


def run_wav_file(
    wav_path: str,
    cfg: Optional[PipelineConfig] = None,
    energy_models: str = "both",  # "arm" | "laptop" | "both"
    viz: str = "plotly",  # "mpl" | "plotly" | "none"
) -> Dict[str, Any]:
    """
    Run the always-on graph on a WAV file source and return a structured result.
    """
    cfg = cfg or PipelineConfig()
    params = _shared_params_from_config(cfg)
    g = build_always_on_graph(params)

    # Feed PCM events iterator to STFT node id ("stft")
    inputs = {"stft": wav_pcm_events(wav_path)}
    report = run_instrumented_event_mode(g, inputs, cfg)
    energies = compare_energy_models(report, params, which=energy_models)

    visualize(report, params, energies, backend=viz)

    # Return a summarized result
    return {
        "mel_frames": report.mel_frames,
        "per_node": {k: vars(v) for k, v in report.per_node.items()},
        "energy": [{"model": e.model_name, "total_nJ": e.total_nj, "per_node_nJ": e.per_node_nj} for e in energies],
    }


def run_mic_live(
    duration_s: float = 15.0,
    cfg: Optional[PipelineConfig] = None,
    energy_models: str = "arm",
    viz: str = "mpl",
) -> Dict[str, Any]:
    """
    Run the always-on graph on a live microphone (blocking capture for duration_s).
    """
    cfg = cfg or PipelineConfig()
    params = _shared_params_from_config(cfg)
    g = build_always_on_graph(params)

    inputs = {"stft": mic_pcm_events(duration_s=duration_s, sample_rate_hz=cfg.fe.sample_rate_hz)}
    report = run_instrumented_event_mode(g, inputs, cfg)
    energies = compare_energy_models(report, params, which=energy_models)

    visualize(report, params, energies, backend=viz)

    return {
        "mel_frames": report.mel_frames,
        "per_node": {k: vars(v) for k, v in report.per_node.items()},
        "energy": [{"model": e.model_name, "total_nJ": e.total_nj, "per_node_nJ": e.per_node_nj} for e in energies],
    }


# ----------------------------
# CLI
# ----------------------------

def _add_common_frontend_args(sp: argparse.ArgumentParser):
    sp.add_argument("--sr", "--sample-rate", dest="sample_rate_hz", type=int, default=16000)
    sp.add_argument("--n_fft", type=int, default=256)
    sp.add_argument("--hop", type=str, default="10 ms")
    sp.add_argument("--n_mels", type=int, default=32)
    sp.add_argument("--fmin_hz", type=float, default=0.0)
    sp.add_argument("--fmax_hz", type=float, default=None)
    sp.add_argument("--window", type=str, default="hann")
    sp.add_argument("--mel-log", dest="mel_log", action="store_true", default=True)
    sp.add_argument("--no-mel-log", dest="mel_log", action="store_false")

    sp.add_argument("--vad-window", type=str, default="30 ms")
    sp.add_argument("--vad-min-bands", type=int, default=3)

    sp.add_argument("--kws-tau-m", type=str, default="10 ms")
    sp.add_argument("--kws-v-th", type=float, default=0.3)
    sp.add_argument("--kws-v-reset", type=float, default=0.0)
    sp.add_argument("--kws-r-m", type=float, default=1.0)
    sp.add_argument("--kws-refractory", type=str, default="2 ms")

    sp.add_argument("--viz", type=str, choices=["mpl", "plotly", "none"], default="mpl")
    sp.add_argument("--energy", type=str, choices=["arm", "laptop", "both"], default="both")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="ef-audio-demo", description="Always-on audio demo: shared STFT->Mel frontend with VAD and KWS heads")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_file = sub.add_parser("file", help="Run offline on a WAV file")
    p_file.add_argument("--path", type=str, default="examples/wakeword/audio.wav")
    _add_common_frontend_args(p_file)

    p_mic = sub.add_parser("mic", help="Run live microphone capture (blocking)")
    p_mic.add_argument("--duration", type=float, default=15.0, help="Capture duration in seconds")
    _add_common_frontend_args(p_mic)

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

    if args.cmd == "file":
        res = run_wav_file(args.path, cfg=cfg, energy_models=args.energy, viz=args.viz)
        # Print a compact summary
        print("mel_frames:", res["mel_frames"])
        for k, m in res["per_node"].items():
            print(f"node {k}: in={m['in_events']} out={m['out_events']} time_s={m['wall_time_s']:.6f}")
        for e in res["energy"]:
            print(f"energy[{e['model']}] total_nJ={e['total_nJ']:.2f} per_node={e['per_node_nJ']}")
        return 0

    if args.cmd == "mic":
        res = run_mic_live(duration_s=args.duration, cfg=cfg, energy_models=args.energy, viz=args.viz)
        print("mel_frames:", res["mel_frames"])
        for k, m in res["per_node"].items():
            print(f"node {k}: in={m['in_events']} out={m['out_events']} time_s={m['wall_time_s']:.6f}")
        for e in res["energy"]:
            print(f"energy[{e['model']}] total_nJ={e['total_nJ']:.2f} per_node={e['per_node_nJ']}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())