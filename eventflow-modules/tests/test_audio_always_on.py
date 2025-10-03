import unittest
import math
from typing import Iterator, Tuple, Dict, List

# Event type alias consistent with core runtime
Event = Tuple[int, int, float, dict]

from eventflow_modules.audio.always_on import (
    build_always_on_graph,
    PipelineConfig,
    FrontendConfig,
    VADConfig,
    KWSConfig,
    run_wav_file,
    run_instrumented_event_mode,
    main as demo_main,
)

def sine_pcm(freq_hz: int = 1000, dur_ms: int = 200, sr: int = 16000) -> Iterator[Event]:
    """Generate PCM sample events compatible with STFT input."""
    n = int(sr * (dur_ms / 1000.0))
    for i in range(n):
        t_ns = int(i * 1e9 / sr)
        yield (t_ns, 0, math.sin(2.0 * math.pi * freq_hz * i / sr), {"unit": "pcm"})

class TestAlwaysOnAudio(unittest.TestCase):
    def test_build_graph_shared_frontend(self):
        g = build_always_on_graph()
        # Nodes present
        for nid in ("stft", "mel", "vad", "kws"):
            self.assertIn(nid, g.nodes, f"Missing node {nid}")
        # At least the expected three connections out of stft/mel
        # stft.spec -> mel.in
        # mel.mel -> vad.a, vad.b, mel.mel -> kws.in
        self.assertGreaterEqual(len(g.edges), 3)

    def test_run_instrumented_with_sine_pcm(self):
        cfg = PipelineConfig(
            fe=FrontendConfig(sample_rate_hz=16000, n_fft=128, hop="8 ms", n_mels=16),
            vad=VADConfig(window="30 ms", min_bands=2),
            kws=KWSConfig(tau_m="10 ms", v_th=0.3),
        )
        params = {
            "sample_rate_hz": cfg.fe.sample_rate_hz,
            "n_fft": cfg.fe.n_fft,
            "hop": cfg.fe.hop,
            "n_mels": cfg.fe.n_mels,
            "fmin_hz": cfg.fe.fmin_hz,
            "fmax_hz": cfg.fe.fmax_hz,
            "mel_log": cfg.fe.mel_log,
            "window": cfg.fe.window,
            "vad_window": cfg.vad.window,
            "vad_min_bands": cfg.vad.min_bands,
            "kws_tau_m": cfg.kws.tau_m,
            "kws_v_th": cfg.kws.v_th,
            "kws_v_reset": cfg.kws.v_reset,
            "kws_r_m": cfg.kws.r_m,
            "kws_refractory": cfg.kws.refractory,
        }
        g = build_always_on_graph(params)
        report = run_instrumented_event_mode(g, {"stft": sine_pcm(1200, 180, 16000)}, cfg)
        # Basic assertions
        self.assertGreater(report.mel_frames, 0)
        self.assertIn("stft", report.per_node)
        self.assertIn("mel", report.per_node)
        # VAD and/or KWS may be sparse but should be present in outputs dict
        self.assertIn("mel", report.outputs)
        self.assertIn("vad", report.outputs)
        self.assertIn("kws", report.outputs)

    def test_run_wav_file_smoke(self):
        # Use the repository's example WAV
        wav_path = "examples/wakeword/audio.wav"
        cfg = PipelineConfig(
            fe=FrontendConfig(sample_rate_hz=16000, n_fft=128, hop="10 ms", n_mels=16),
            vad=VADConfig(window="30 ms", min_bands=3),
            kws=KWSConfig(tau_m="10 ms", v_th=0.3),
        )
        res = run_wav_file(wav_path, cfg=cfg, energy_models="both", viz="none")
        self.assertIn("mel_frames", res)
        self.assertGreater(res["mel_frames"], 0)
        self.assertIn("per_node", res)
        self.assertIn("stft", res["per_node"])
        self.assertIn("mel", res["per_node"])
        self.assertIn("energy", res)
        self.assertGreaterEqual(len(res["energy"]), 1)  # both -> 2

    def test_cli_main_file_returns_zero(self):
        # Exercise the CLI entrypoint in "file" mode without plotting
        rc = demo_main([
            "file",
            "--path", "examples/wakeword/audio.wav",
            "--viz", "none",
            "--energy", "both",
            "--n_fft", "64",
            "--n_mels", "12",
            "--hop", "8 ms",
            "--sr", "16000",
        ])
        self.assertEqual(rc, 0)

if __name__ == "__main__":
    unittest.main()