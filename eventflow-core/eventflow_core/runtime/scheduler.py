from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Callable, Iterator, Optional
from ..eir.graph import EIRGraph
from ..eir.ops import (
    step_lif, LIFState, step_exp_syn, step_delay, Event,
    step_stft, step_mel, build_mel_filters,
    step_xy_to_ch, step_shift_xy,
)
from ..eir.types import time_to_ns

# Optional Rust acceleration
try:
    from .._rust import is_enabled as _ef_native_enabled, native as _ef_native  # type: ignore
except Exception:
    def _ef_native_enabled() -> bool:
        return False
    _ef_native = None  # type: ignore

@dataclass
class ExecNode:
    kind: str
    fn: Callable
    state: Optional[object]

def build_exec_nodes(g: EIRGraph) -> Dict[str, ExecNode]:
    nodes: Dict[str, ExecNode] = {}
    for nid, node in g.nodes.items():
        k,p = node.op.kind, node.op.params
        if k=="lif":
            st=LIFState(time_to_ns(p["tau_m"]),p["v_th"],p["v_reset"],p["r_m"],time_to_ns(p["refractory"]))
            nodes[nid] = ExecNode(k, lambda it,st=st:step_lif(it,st),st)
        elif k=="exp_syn":
            tau=time_to_ns(p["tau_s"]); w=p["weight"]; nodes[nid]=ExecNode(k,lambda it,tau=tau,w=w:step_exp_syn(it,tau,w),None)
        elif k=="delay":
            d=time_to_ns(p["delay"]); nodes[nid]=ExecNode(k,lambda it,d=d:step_delay(it,d),None)
        elif k=="fuse":
            win = time_to_ns(p["window"]); minc = int(p["min_count"])
            if _ef_native_enabled() and _ef_native is not None and hasattr(_ef_native, "fuse_coincidence_i64"):
                def _fuse_native(it_a: Iterator[Event], it_b: Iterator[Event]):
                    import numpy as np
                    t_a = [int(t) for (t, _, _, _) in it_a]
                    t_b = [int(t) for (t, _, _, _) in it_b]
                    if not t_a and not t_b:
                        return
                    t_a_arr = np.asarray(t_a, dtype=np.int64) if t_a else np.empty((0,), dtype=np.int64)
                    t_b_arr = np.asarray(t_b, dtype=np.int64) if t_b else np.empty((0,), dtype=np.int64)
                    t_out, v_out = _ef_native.fuse_coincidence_i64(t_a_arr, t_b_arr, int(win), int(minc))
                    for t, val in zip(t_out.tolist(), v_out.tolist()):
                        yield (int(t), 0, float(val), {"unit": "coincidence"})
                nodes[nid] = ExecNode(k, _fuse_native, None)
            else:
                def _fuse(it_a: Iterator[Event], it_b: Iterator[Event]):
                    import heapq
                    heap = []
                    buf_a, buf_b = [], []
                    for t, c, v, meta in it_a:
                        heapq.heappush(heap, (t, ("a", (t, c, v, meta))))
                    for t, c, v, meta in it_b:
                        heapq.heappush(heap, (t, ("b", (t, c, v, meta))))
                    while heap:
                        t, (src, ev) = heapq.heappop(heap)
                        buf = buf_a if src == "a" else buf_b
                        buf.append(ev)
                        cutoff = t - win
                        buf_a[:] = [e for e in buf_a if e[0] >= cutoff]
                        buf_b[:] = [e for e in buf_b if e[0] >= cutoff]
                        if len(buf_a) + len(buf_b) >= minc and buf_a and buf_b:
                            yield (t, 0, 1.0, {"unit": "coincidence"})
                nodes[nid] = ExecNode(k, _fuse, None)
        elif k=="stft":
            n_fft = int(p["n_fft"]); hop_ns = time_to_ns(p["hop"]); sr = int(p["sample_rate_hz"]); win = p.get("window","hann")
            nodes[nid] = ExecNode(k, lambda it, n_fft=n_fft, hop_ns=hop_ns, sr=sr, win=win: step_stft(it, n_fft, hop_ns, sr, win), None)
        elif k=="mel":
            n_fft = int(p["n_fft"]); n_mels = int(p["n_mels"]); sr = int(p["sample_rate_hz"])
            fmin = float(p.get("fmin_hz", 0.0)); fmax = float(p.get("fmax_hz") or (sr/2))
            log = bool(p.get("log", True))
            n_bins = n_fft // 2 + 1
            filters = build_mel_filters(n_fft, n_mels, sr, fmin, fmax)
            nodes[nid] = ExecNode(k, lambda it, filters=filters, n_bins=n_bins, log=log: step_mel(it, filters, n_bins, log), None)
        elif k=="xy_to_ch":
            w = int(p["width"]); h = int(p["height"])
            nodes[nid] = ExecNode(k, lambda it, w=w, h=h: step_xy_to_ch(it, w, h), None)
        elif k=="shift_xy":
            dx = int(p.get("dx", 0)); dy = int(p.get("dy", 0))
            w = int(p.get("width", 128)); h = int(p.get("height", 128))
            nodes[nid] = ExecNode(k, lambda it, dx=dx, dy=dy, w=w, h=h: step_shift_xy(it, dx, dy, w, h), None)
    return nodes
