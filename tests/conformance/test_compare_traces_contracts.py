from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
EF_CLI = REPO_ROOT / "eventflow-cli" / "ef.py"


def _run_ef(args: list[str]) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-u", str(EF_CLI), "--json"] + [str(a) for a in args]
    return subprocess.run(cmd, cwd=str(REPO_ROOT), text=True, capture_output=True, check=False)


def _write_trace(path: Path, *, ts2: int = 100, val2: float = 1.0, with_header: bool = True) -> None:
    if with_header:
        header = {
            "header": {
                "schema_version": "0.1.0",
                "dims": ["ch"],
                "units": {"time": "us", "value": "dimensionless"},
                "dtype": "f32",
                "layout": "coo",
            }
        }
    records = [
        {"ts": 0, "idx": [0], "val": 1.0},
        {"ts": ts2, "idx": [0], "val": val2},
    ]
    with open(path, "w", encoding="utf-8") as f:
        if with_header:
            f.write(json.dumps(header) + "\n")
        for rec in records:
            f.write(json.dumps(rec) + "\n")


@pytest.mark.conformance
def test_compare_traces_exact_match_ok(tmp_path: Path) -> None:
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    _write_trace(a)
    _write_trace(b)

    proc = _run_ef(["compare-traces", "--golden", a, "--candidate", b])
    assert proc.returncode == 0, proc.stderr
    assert proc.stderr.strip() == ""
    payload = json.loads(proc.stdout)
    assert payload["ok"] is True
    assert payload["mismatch_count"] == 0


@pytest.mark.conformance
def test_compare_traces_tolerance_violation(tmp_path: Path) -> None:
    golden = tmp_path / "golden.jsonl"
    candidate = tmp_path / "candidate.jsonl"
    _write_trace(golden, ts2=100, val2=1.0)
    _write_trace(candidate, ts2=500, val2=4.0)

    proc = _run_ef(
        [
            "compare-traces",
            "--golden",
            golden,
            "--candidate",
            candidate,
            "--eps-time-us",
            "10",
            "--eps-numeric",
            "1e-9",
        ]
    )
    assert proc.returncode == 1
    assert proc.stderr.strip() == ""
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert payload["mismatch_count"] > 0


@pytest.mark.conformance
def test_compare_traces_malformed_header_json_error(tmp_path: Path) -> None:
    golden = tmp_path / "golden.jsonl"
    malformed = tmp_path / "malformed.jsonl"
    _write_trace(golden)
    _write_trace(malformed, with_header=False)

    proc = _run_ef(["compare-traces", "--golden", golden, "--candidate", malformed])
    assert proc.returncode == 1
    assert proc.stderr.strip() == ""
    payload = json.loads(proc.stdout)
    assert payload["ok"] is False
    assert "error" in payload


@pytest.mark.conformance
def test_compare_traces_json_stdout_has_no_extra_text(tmp_path: Path) -> None:
    a = tmp_path / "a.jsonl"
    b = tmp_path / "b.jsonl"
    _write_trace(a)
    _write_trace(b)

    proc = _run_ef(["compare-traces", "--golden", a, "--candidate", b])
    assert proc.returncode == 0, proc.stderr
    assert proc.stderr.strip() == ""
    stdout = proc.stdout.strip()
    assert stdout.startswith("{") and stdout.endswith("}")
