from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from .conftest import assert_json_success, parse_json_stdout, run_ef


@pytest.mark.e2e
def test_e2e_audio_sal_run_compare(repo_root: Path, tmp_path: Path) -> None:
    eir = repo_root / "examples" / "wakeword" / "eir.json"
    assert eir.is_file()

    wav = tmp_path / "audio.wav"
    wav_gen = repo_root / "tools" / "gen_sine_wav.py"
    gen = subprocess.run(
        [sys.executable, str(wav_gen), "--path", str(wav)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )

    if gen.returncode == 0 and wav.is_file():
        norm = tmp_path / "audio.norm.jsonl"
        tele = tmp_path / "audio.telemetry.json"
        sal = run_ef(
            [
                "sal-stream",
                "--uri",
                f"audio.mic://file?path={wav}&window_ms=20&hop_ms=10&bands=32",
                "--out",
                str(norm),
                "--telemetry-out",
                str(tele),
            ]
        )
        if sal.returncode == 0:
            sal_payload = assert_json_success(sal)
            assert Path(sal_payload["out"]).is_file()
            assert sal_payload["telemetry"]["count"] > 0
            clock = sal_payload["telemetry"]["clock"]
            assert "jitter_p50_us" in clock
            assert "jitter_p95_us" in clock
            assert "jitter_p99_us" in clock
            input_path = norm
        else:
            payload = parse_json_stdout(sal)
            assert payload["ok"] is False
            # Optional dependency path: fall back to checked-in sample in fast environments.
            if "scipy" not in str(payload.get("error", "")).lower():
                raise AssertionError(f"unexpected sal-stream failure: {payload}")
            input_path = repo_root / "examples" / "wakeword" / "traces" / "inputs" / "audio_sample.jsonl"
            assert input_path.is_file()
    else:
        # Fallback path: use checked-in sample JSONL if WAV generation is unavailable.
        input_path = repo_root / "examples" / "wakeword" / "traces" / "inputs" / "audio_sample.jsonl"
        assert input_path.is_file()

    trace = tmp_path / "wakeword.trace.jsonl"
    run = run_ef(
        [
            "run",
            "--eir",
            str(eir),
            "--backend",
            "cpu-sim",
            "--input",
            str(input_path),
            "--trace-out",
            str(trace),
        ]
    )
    run_payload = assert_json_success(run)
    assert run_payload["status"] == "ok"
    assert Path(run_payload["trace_path"]).is_file()
    assert int(run_payload["count"]) >= 1

    compare = run_ef(
        [
            "compare-traces",
            "--golden",
            str(trace),
            "--candidate",
            str(trace),
            "--eps-time-us",
            "100",
            "--eps-numeric",
            "1e-5",
        ]
    )
    compare_payload = parse_json_stdout(compare)
    assert compare.returncode == 0, f"compare failed: {compare.stderr}"
    assert compare_payload["ok"] is True
