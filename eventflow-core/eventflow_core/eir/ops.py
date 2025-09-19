from __future__ import annotations
from dataclasses import dataclass
from typing import Iterator, Tuple, Optional
from .types import OpDef, Port, time_to_ns
import math

Event = Tuple[int, int, float, dict]

@dataclass
class LIFNeuron:
    name: str; tau_m: str="10 ms"; v_th: float=1.0; v_reset: float=0.0; r_m: float=1.0; refractory: str="2 ms"
    def as_op(self) -> OpDef: return OpDef("lif", self.name, [Port("in")], [Port("spike")], self.__dict__)

@dataclass
class ExpSynapse:
    name: str; tau_s: str="5 ms"; weight: float=1.0
    def as_op(self) -> OpDef: return OpDef("exp_syn", self.name, [Port("pre")], [Port("post")], self.__dict__)

@dataclass
class DelayLine:
    name: str; delay: str="1 ms"
    def as_op(self) -> OpDef: return OpDef("delay", self.name, [Port("in")], [Port("out")], self.__dict__)

@dataclass
class EventFuse:
    name: str; window: str="50 ms"; min_count: int=2
    def as_op(self) -> OpDef: return OpDef("fuse", self.name, [Port("a"), Port("b")], [Port("out")], self.__dict__)

def step_exp_syn(inputs: Iterator[Event], tau_s_ns: int, weight: float) -> Iterator[Event]:
    for t, ch, val, meta in inputs: yield (t, ch, weight * val, {**meta, "syn":"exp", "tau_s_ns":tau_s_ns})

def step_delay(inputs: Iterator[Event], delay_ns: int) -> Iterator[Event]:
    for t, ch, val, meta in inputs: yield (t + delay_ns, ch, val, meta)

class LIFState:
    __slots__ = ("v", "t_last_spike_ns", "t_prev_ns", "ref_ns", "tau_m_ns", "r_m", "v_th", "v_reset")
    def __init__(self, tau_m_ns: int, v_th: float, v_reset: float, r_m: float, refractory_ns: int):
        self.v, self.t_last_spike_ns, self.t_prev_ns = 0.0, -10**18, 0
        self.ref_ns, self.tau_m_ns, self.r_m, self.v_th, self.v_reset = refractory_ns, tau_m_ns, r_m, v_th, v_reset

def step_lif(inputs: Iterator[Event], state: LIFState) -> Iterator[Event]:
    for t, ch, val, meta in inputs:
        if state.tau_m_ns <= 0: alpha = 0.0
        else: dt = max(0, t - state.t_prev_ns); alpha = pow(2.71828, -dt / state.tau_m_ns)
        state.v = state.v * alpha + state.r_m * val
        state.t_prev_ns = t
        # Block spikes at or within the refractory interval (<=) for deterministic single-spike behavior in tests
        if t - state.t_last_spike_ns <= state.ref_ns: continue
        if state.v >= state.v_th:
            state.v, state.t_last_spike_ns = state.v_reset, t
            yield (t, 0, 1.0, {"unit":"spike"})

@dataclass
class STFT:
    name: str
    n_fft: int = 256
    hop: str = "10 ms"
    sample_rate_hz: int = 16000
    window: str = "hann"
    def as_op(self) -> OpDef:
        return OpDef("stft", self.name, [Port("in")], [Port("spec")], self.__dict__)

@dataclass
class MelBands:
    name: str
    n_fft: int = 256
    n_mels: int = 32
    sample_rate_hz: int = 16000
    fmin_hz: float = 0.0
    fmax_hz: Optional[float] = None
    log: bool = True
    def as_op(self) -> OpDef:
        return OpDef("mel", self.name, [Port("in")], [Port("mel")], self.__dict__)

def _hann_window(N: int) -> list[float]:
    if N <= 1:
        return [1.0] * max(N, 1)
    return [0.5 - 0.5 * math.cos(2.0 * math.pi * n / (N - 1)) for n in range(N)]

def _round_div(a: int, b: int) -> int:
    return int(round(a / b))

def step_stft(inputs: Iterator[Event], n_fft: int, hop_ns: int, sample_rate_hz: int, window: str) -> Iterator[Event]:
    # Deterministic software STFT for PCM sample events on ch=0. Missing samples treated as zeros.
    sr = float(sample_rate_hz)
    hop_samples = max(1, int(round(hop_ns * sr / 1e9)))
    w = _hann_window(n_fft) if window == "hann" else [1.0] * n_fft
    next_start = 0
    samples: dict[int, float] = {}
    last_idx = -1

    def emit_frame(start_idx: int):
        nonlocal w
        N = n_fft
        # Preload frame samples with zeros default
        frame = [samples.get(start_idx + n, 0.0) * w[n] for n in range(N)]
        half = N // 2
        t_frame_ns = int(round((start_idx + N) * 1e9 / sr))
        for k in range(0, half + 1):
            re = 0.0
            im = 0.0
            ang_base = 2.0 * math.pi * k / N
            for n in range(N):
                ang = ang_base * n
                c = math.cos(ang)
                s = math.sin(ang)
                x = frame[n]
                re += x * c
                im -= x * s
            mag = math.sqrt(re * re + im * im)
            yield (t_frame_ns, k, mag, {"unit": "mag", "n_fft": N})

    for t_ns, ch, val, meta in inputs:
        # Map timestamp to nearest sample index according to provided sample rate.
        i = int(round((t_ns * sr) / 1e9))
        last_idx = max(last_idx, i)
        samples[i] = val
        # Emit as many frames as available
        while last_idx >= next_start + n_fft - 1:
            for ev in emit_frame(next_start):
                yield ev
            next_start += hop_samples
    # No additional flush beyond last full frame (consistent STFT semantics)

def _hz_to_mel(f: float) -> float:
    return 2595.0 * math.log10(1.0 + f / 700.0)

def _mel_to_hz(m: float) -> float:
    return 700.0 * (10.0 ** (m / 2595.0) - 1.0)

def build_mel_filters(n_fft: int, n_mels: int, sample_rate_hz: int, fmin_hz: float, fmax_hz: float) -> list[list[float]]:
    # Triangular mel filters over [fmin, fmax]
    n_bins = n_fft // 2 + 1
    sr = float(sample_rate_hz)
    fmin_mel = _hz_to_mel(fmin_hz)
    fmax_mel = _hz_to_mel(fmax_hz)
    mel_points = [fmin_mel + (fmax_mel - fmin_mel) * i / (n_mels + 1) for i in range(n_mels + 2)]
    hz_points = [_mel_to_hz(m) for m in mel_points]
    bin_points = [int(math.floor((n_fft + 1) * f / sr)) for f in hz_points]
    filters: list[list[float]] = [[0.0 for _ in range(n_bins)] for _ in range(n_mels)]
    for m in range(1, n_mels + 1):
        f_m_minus = bin_points[m - 1]
        f_m = bin_points[m]
        f_m_plus = bin_points[m + 1]
        for k in range(max(f_m_minus, 0), min(f_m_plus, n_bins - 1) + 1):
            if k < f_m:
                denom = (f_m - f_m_minus) or 1
                filters[m - 1][k] = (k - f_m_minus) / denom
            else:
                denom = (f_m_plus - f_m) or 1
                filters[m - 1][k] = (f_m_plus - k) / denom
            if filters[m - 1][k] < 0.0:
                filters[m - 1][k] = 0.0
    return filters

def step_mel(inputs: Iterator[Event], filters: list[list[float]], n_bins: int, log: bool) -> Iterator[Event]:
    # Group STFT magnitude events by frame time, aggregate bins, then apply mel filters.
    current_t = None
    spec = [0.0] * n_bins
    def flush_spec(ts: int):
        nonlocal spec
        for m, filt in enumerate(filters):
            e = 0.0
            # Weighted sum across bins
            for k in range(n_bins):
                e += spec[k] * filt[k]
            if log:
                e = math.log(max(e, 1e-12))
            yield (ts, m, e, {"unit": "mel"})
        spec = [0.0] * n_bins

    for t_ns, ch, val, meta in inputs:
        if current_t is None:
            current_t = t_ns
        if t_ns != current_t:
            for ev in flush_spec(current_t):
                yield ev
            current_t = t_ns
        if 0 <= ch < n_bins:
            spec[ch] = val
    if current_t is not None:
        for ev in flush_spec(current_t):
            yield ev

@dataclass
class XYToChannel:
    name: str
    width: int = 128
    height: int = 128
    def as_op(self) -> OpDef:
        return OpDef("xy_to_ch", self.name, [Port("in")], [Port("ch")], self.__dict__)

@dataclass
class ShiftXY:
    name: str
    dx: int = 0
    dy: int = 0
    width: int = 128
    height: int = 128
    def as_op(self) -> OpDef:
        return OpDef("shift_xy", self.name, [Port("in")], [Port("out")], self.__dict__)

def step_xy_to_ch(inputs: Iterator[Event], width: int, height: int) -> Iterator[Event]:
    max_x = width - 1
    max_y = height - 1
    for t, ch, val, meta in inputs:
        x = int(meta.get("x", -1))
        y = int(meta.get("y", -1))
        if 0 <= x <= max_x and 0 <= y <= max_y:
            ch_out = y * width + x
            yield (t, ch_out, 1.0 if val is None else float(val), {**meta, "w": width, "h": height})

def step_shift_xy(inputs: Iterator[Event], dx: int, dy: int, width: int, height: int) -> Iterator[Event]:
    max_x = width - 1
    max_y = height - 1
    for t, ch, val, meta in inputs:
        if ch < 0:
            continue
        x = ch % width
        y = ch // width
        nx = min(max(x + dx, 0), max_x)
        ny = min(max(y + dy, 0), max_y)
        ch_out = ny * width + nx
        yield (t, ch_out, val, meta)
