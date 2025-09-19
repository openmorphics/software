import unittest, math
from collections import defaultdict
from eventflow_core.eir.graph import EIRGraph
from eventflow_core.eir.ops import STFT, MelBands
from eventflow_core.runtime.exec import run_event_mode

def sine_pcm(freq_hz=1000, dur_ms=200, sr=16000):
    n = int(sr * (dur_ms / 1000.0))
    for i in range(n):
        t_ns = int(i * 1e9 / sr)
        yield (t_ns, 0, math.sin(2.0 * math.pi * freq_hz * i / sr), {"unit": "pcm"})

class TestAudioOps(unittest.TestCase):
    def test_stft_peak_bin(self):
        n_fft = 128; sr = 16000; f = 1000
        g = EIRGraph()
        g.add_node("stft", STFT("stft", n_fft=n_fft, hop="8 ms", sample_rate_hz=sr).as_op())
        out = run_event_mode(g, {"stft": sine_pcm(f, dur_ms=200, sr=sr)})
        evs = out["stft"]
        self.assertGreater(len(evs), 0)
        frames = defaultdict(list)
        for t, ch, val, meta in evs:
            frames[t].append((ch, val))
        last_t = sorted(frames.keys())[-1]
        bins = frames[last_t]
        kmax, vmax = max(bins, key=lambda kv: kv[1])
        expected = round(f * n_fft / sr)
        self.assertLessEqual(abs(kmax - expected), 1)

    def test_mel_emit_counts(self):
        n_fft = 64; n_mels = 10; sr = 16000
        g = EIRGraph()
        g.add_node("stft", STFT("stft", n_fft=n_fft, hop="10 ms", sample_rate_hz=sr).as_op())
        g.add_node("mel", MelBands("mel", n_fft=n_fft, n_mels=n_mels, sample_rate_hz=sr).as_op())
        g.connect("stft", "spec", "mel", "in")
        out = run_event_mode(g, {"stft": sine_pcm(800, dur_ms=120, sr=sr)})
        evs = out["mel"]
        self.assertGreater(len(evs), 0)
        frames = {}
        for t, ch, val, meta in evs:
            frames.setdefault(t, set()).add(ch)
        # At least one frame with full n_mels coefficients
        self.assertTrue(any(len(chs) == n_mels for chs in frames.values()))
