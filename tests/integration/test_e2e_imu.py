from __future__ import annotations

from pathlib import Path

import pytest

from .conftest import assert_json_success, parse_json_stdout, run_ef


@pytest.mark.e2e
def test_e2e_imu_sal_run_compare(repo_root: Path, tmp_path: Path) -> None:
    eir = repo_root / "examples" / "anomaly_timeseries" / "eir.json"
    csv_path = repo_root / "examples" / "robotics_slam" / "traces" / "inputs" / "imu_sample.csv"
    assert eir.is_file()
    assert csv_path.is_file()

    norm = tmp_path / "imu.norm.jsonl"
    tele = tmp_path / "imu.telemetry.json"
    trace = tmp_path / "imu.trace.jsonl"

    sal = run_ef(
        [
            "sal-stream",
            "--uri",
            f"imu.6dof://file?path={csv_path}",
            "--out",
            str(norm),
            "--telemetry-out",
            str(tele),
        ]
    )
    sal_payload = assert_json_success(sal)
    assert Path(sal_payload["out"]).is_file()
    assert sal_payload["telemetry"]["count"] > 0
    clock = sal_payload["telemetry"]["clock"]
    assert "jitter_p50_us" in clock
    assert "jitter_p95_us" in clock
    assert "jitter_p99_us" in clock

    run = run_ef(
        [
            "run",
            "--eir",
            str(eir),
            "--backend",
            "cpu-sim",
            "--input",
            str(norm),
            "--trace-out",
            str(trace),
        ]
    )
    run_payload = assert_json_success(run)
    assert run_payload["status"] == "ok"
    assert Path(run_payload["trace_path"]).is_file()

    compare = run_ef(
        [
            "compare-traces",
            "--golden",
            str(trace),
            "--candidate",
            str(trace),
        ]
    )
    compare_payload = parse_json_stdout(compare)
    assert compare.returncode == 0, f"compare failed: {compare.stderr}"
    assert compare_payload["ok"] is True
