from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import assert_json_success, parse_json_stdout, run_ef


@pytest.mark.e2e
def test_e2e_vision_sal_build_run_compare(repo_root: Path, tmp_path: Path) -> None:
    eir = repo_root / "examples" / "vision_optical_flow" / "eir.json"
    src = repo_root / "examples" / "vision_optical_flow" / "traces" / "inputs" / "vision_sample.jsonl"
    assert eir.is_file()
    assert src.is_file()

    norm = tmp_path / "vision.norm.jsonl"
    tele = tmp_path / "vision.telemetry.json"
    plan = tmp_path / "vision.plan.json"
    trace_a = tmp_path / "vision.trace.a.jsonl"
    trace_b = tmp_path / "vision.trace.b.jsonl"

    sal = run_ef(
        [
            "sal-stream",
            "--uri",
            f"vision.dvs://file?format=jsonl&path={src}",
            "--out",
            str(norm),
            "--telemetry-out",
            str(tele),
        ]
    )
    sal_payload = assert_json_success(sal)
    assert Path(sal_payload["out"]).is_file()
    assert Path(tele).is_file()
    assert sal_payload["telemetry"]["count"] > 0
    clock = sal_payload["telemetry"]["clock"]
    assert "jitter_p50_us" in clock
    assert "jitter_p95_us" in clock
    assert "jitter_p99_us" in clock

    build = run_ef(
        [
            "build",
            "--eir",
            str(eir),
            "--backend",
            "cpu-sim",
            "--plan-out",
            str(plan),
        ]
    )
    build_payload = assert_json_success(build)
    assert Path(build_payload["plan_out"]).is_file()

    run1 = run_ef(
        [
            "run",
            "--eir",
            str(eir),
            "--backend",
            "cpu-sim",
            "--input",
            str(norm),
            "--trace-out",
            str(trace_a),
            "--plan",
            str(plan),
        ]
    )
    run1_payload = assert_json_success(run1)
    assert run1_payload["status"] == "ok"
    assert Path(run1_payload["trace_path"]).is_file()

    run2 = run_ef(
        [
            "run",
            "--eir",
            str(eir),
            "--backend",
            "cpu-sim",
            "--input",
            str(norm),
            "--trace-out",
            str(trace_b),
            "--plan",
            str(plan),
        ]
    )
    run2_payload = assert_json_success(run2)
    assert run2_payload["status"] == "ok"
    assert Path(run2_payload["trace_path"]).is_file()

    compare = run_ef(
        [
            "compare-traces",
            "--golden",
            str(trace_a),
            "--candidate",
            str(trace_b),
            "--eps-time-us",
            "50",
            "--eps-numeric",
            "1e-5",
        ]
    )
    compare_payload = parse_json_stdout(compare)
    assert compare.returncode == 0, f"compare failed: {compare.stderr}"
    assert compare_payload["ok"] is True
    assert compare_payload["mismatch_count"] == 0
