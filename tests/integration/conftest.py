from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
EF_CLI = REPO_ROOT / "eventflow-cli" / "ef.py"


@pytest.fixture
def repo_root() -> Path:
    return REPO_ROOT


def run_ef(
    args: list[str],
    *,
    json_mode: bool = True,
    cwd: Path | None = None,
    env_overrides: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, "-u", str(EF_CLI)]
    if json_mode:
        cmd.append("--json")
    cmd.extend(str(a) for a in args)

    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)

    return subprocess.run(
        cmd,
        cwd=str(cwd or REPO_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def parse_json_stdout(proc: subprocess.CompletedProcess[str]) -> Any:
    stdout = proc.stdout.strip()
    assert stdout, f"expected JSON stdout, got empty output (stderr={proc.stderr!r})"
    return json.loads(stdout)


def assert_json_success(proc: subprocess.CompletedProcess[str]) -> Any:
    assert proc.returncode == 0, f"unexpected rc={proc.returncode}; stderr={proc.stderr!r}"
    payload = parse_json_stdout(proc)
    assert proc.stderr.strip() == "", f"unexpected stderr in JSON mode: {proc.stderr!r}"
    return payload


def assert_json_error(proc: subprocess.CompletedProcess[str], *, rc: int) -> Any:
    assert proc.returncode == rc, f"unexpected rc={proc.returncode}; stderr={proc.stderr!r}"
    payload = parse_json_stdout(proc)
    assert proc.stderr.strip() == "", f"unexpected stderr in JSON mode: {proc.stderr!r}"
    assert isinstance(payload, dict), f"expected object JSON payload, got: {payload!r}"
    assert payload.get("ok") is False, f"expected ok=false payload, got: {payload!r}"
    assert "error" in payload, f"expected error field in payload, got: {payload!r}"
    return payload
