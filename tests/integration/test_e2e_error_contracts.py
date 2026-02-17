from __future__ import annotations

import json
from pathlib import Path

import pytest

from .conftest import assert_json_error, parse_json_stdout, run_ef


def _write_trace(path: Path, *, val: float) -> None:
    header = {
        "header": {
            "schema_version": "0.1.0",
            "dims": ["ch"],
            "units": {"time": "us", "value": "dimensionless"},
            "dtype": "f32",
            "layout": "coo",
        }
    }
    events = [
        {"ts": 0, "idx": [0], "val": val},
        {"ts": 100, "idx": [0], "val": val},
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(header) + "\n")
        for ev in events:
            f.write(json.dumps(ev) + "\n")


@pytest.mark.e2e
def test_unknown_backend_json_error_contract(repo_root: Path, tmp_path: Path) -> None:
    eir = repo_root / "examples" / "vision_optical_flow" / "eir.json"
    plan = tmp_path / "bad.plan.json"
    proc = run_ef(
        [
            "build",
            "--eir",
            str(eir),
            "--backend",
            "unknown-backend",
            "--plan-out",
            str(plan),
        ]
    )
    payload = assert_json_error(proc, rc=1)
    assert "unknown-backend" in payload["error"]
    assert not plan.exists()


@pytest.mark.e2e
def test_invalid_sal_uri_file_json_error_contract(tmp_path: Path) -> None:
    out = tmp_path / "invalid.jsonl"
    proc = run_ef(
        [
            "sal-stream",
            "--uri",
            "vision.dvs://file?format=jsonl&path=/definitely/missing/file.jsonl",
            "--out",
            str(out),
        ]
    )
    payload = assert_json_error(proc, rc=2)
    assert "/definitely/missing/file.jsonl" in payload["error"]


@pytest.mark.e2e
def test_compare_mismatch_returns_nonzero_json_contract(tmp_path: Path) -> None:
    golden = tmp_path / "golden.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    _write_trace(golden, val=1.0)
    _write_trace(candidate, val=9.0)

    proc = run_ef(
        [
            "compare-traces",
            "--golden",
            str(golden),
            "--candidate",
            str(candidate),
            "--eps-time-us",
            "0",
            "--eps-numeric",
            "1e-9",
        ]
    )
    payload = parse_json_stdout(proc)
    assert proc.returncode == 1
    assert proc.stderr.strip() == ""
    assert payload["ok"] is False
    assert payload["mismatch_count"] > 0


@pytest.mark.e2e
def test_build_rejects_python_builder_path_json_error_contract(tmp_path: Path) -> None:
    plan = tmp_path / "bad.plan.json"
    proc = run_ef(
        [
            "build",
            "--eir",
            "tools/gen_sine_wav.py",
            "--backend",
            "cpu-sim",
            "--plan-out",
            str(plan),
        ]
    )
    payload = assert_json_error(proc, rc=2)
    assert "cannot load EIR JSON" in payload["error"]
    assert not plan.exists()


@pytest.mark.e2e
def test_compare_missing_file_returns_io_json_error_contract(tmp_path: Path) -> None:
    proc = run_ef(
        [
            "compare-traces",
            "--golden",
            str(tmp_path / "missing.golden.jsonl"),
            "--candidate",
            str(tmp_path / "missing.candidate.jsonl"),
        ]
    )
    payload = assert_json_error(proc, rc=2)
    assert "No such file or directory" in payload["error"]
