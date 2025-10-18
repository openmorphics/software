import unittest, math, os
from collections import defaultdict
from eventflow_core.runtime.exec import run_event_mode
from eventflow_modules.audio import (
    stft_frontend,
    mel_frontend,
    voice_activity,
    keyword_spotter,
    build_always_on_graph,
    run_instrumented_event_mode,
    PipelineConfig,
)
from eventflow_modules.audio.always_on import main as audio_cli_main

def sine_pcm(freq_hz=1000, dur_ms=200, sr=16000):
    n = int(sr * (dur_ms / 1000.0))
    for i in range(n):
        t_ns = int(i * 1e9 / sr)
        yield (t_ns, 0, math.sin(2.0 * math.pi * freq_hz * i / sr), {"unit": "pcm"})

class TestAudioModules(unittest.TestCase):
    def test_stft_frontend_bin(self):
        g = stft_frontend(None, n_fft=128, hop="8 ms", sample_rate_hz=16000)
        out = run_event_mode(g, {"stft": sine_pcm(1000, dur_ms=200, sr=16000)})
        evs = out["stft"]; self.assertGreater(len(evs), 0)
        frames = defaultdict(list)
        for t, ch, val, meta in evs:
            frames[t].append((ch, val))
        last_t = sorted(frames.keys())[-1]
        bins = frames[last_t]
        kmax, vmax = max(bins, key=lambda kv: kv[1])
        expected = round(1000 * 128 / 16000)
        self.assertLessEqual(abs(kmax - expected), 1)

    def test_vad_pipeline_outputs(self):
        g = voice_activity(None, window="30 ms", min_bands=2, params={"n_fft": 64, "n_mels": 10, "hop": "8 ms", "sample_rate_hz": 16000})
        out = run_event_mode(g, {"stft": sine_pcm(1200, dur_ms=150, sr=16000)})
        self.assertIn("mel", out)
        self.assertIn("vad", out)
        self.assertGreaterEqual(len(out["mel"]), 1)
        self.assertGreaterEqual(len(out["vad"]), 1)

    def test_kws_builds_and_runs(self):
        g = keyword_spotter(None, tau_m="8 ms", v_th=0.2, params={"n_fft": 64, "n_mels": 10, "hop": "8 ms", "sample_rate_hz": 16000})
        out = run_event_mode(g, {"stft": sine_pcm(700, dur_ms=160, sr=16000)})
        # We expect mel features; LIF may or may not spike depending on params
        self.assertIn("mel", out)
        self.assertGreater(len(out["mel"]), 0)

    def test_always_on_smoke(self):
        cfg = PipelineConfig()
        g = build_always_on_graph()
        report = run_instrumented_event_mode(
            g,
            {"stft": sine_pcm(1000, dur_ms=80, sr=16000)},
            cfg,
        )
        self.assertGreaterEqual(report.mel_frames, 0)
        self.assertIn("mel", report.per_node)

    def test_always_on_cli_file_smoke(self):
        wav = "examples/wakeword/audio.wav"
        if not os.path.exists(wav):
            self.skipTest("examples/wakeword/audio.wav not found")
        rc = audio_cli_main(["file", "--path", wav, "--viz", "none", "--energy", "arm"])
        self.assertEqual(rc, 0)
