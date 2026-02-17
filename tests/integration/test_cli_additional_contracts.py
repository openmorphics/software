from __future__ import annotations

import json
from pathlib import Path

import pytest

from .conftest import assert_json_error, assert_json_success, parse_json_stdout, run_ef


@pytest.mark.e2e
def test_cli_profile_and_trace_stats_json_contract(repo_root: Path) -> None:
    trace = repo_root / "examples" / "wakeword" / "traces" / "inputs" / "audio_sample.jsonl"
    assert trace.is_file()

    profile = run_ef(["profile", "--path", str(trace)])
    payload = assert_json_success(profile)
    assert payload["path"] == str(trace)
    assert payload["count"] > 0
    assert "dt" in payload

    alias = run_ef(["trace-stats", "--path", str(trace)])
    alias_payload = assert_json_success(alias)
    assert alias_payload["count"] == payload["count"]


@pytest.mark.e2e
def test_cli_package_then_validate_manifest(repo_root: Path, tmp_path: Path) -> None:
    eir = repo_root / "examples" / "wakeword" / "eir.json"
    golden = repo_root / "examples" / "wakeword" / "traces" / "golden" / "wakeword.golden.jsonl"
    inp = repo_root / "examples" / "wakeword" / "traces" / "inputs" / "audio_sample.jsonl"
    out = tmp_path / "wakeword.efpkg.json"
    assert eir.is_file() and golden.is_file() and inp.is_file()

    pkg = run_ef(
        [
            "package",
            "--eir",
            str(eir),
            "--golden",
            str(golden),
            "--input",
            str(inp),
            "--model-id",
            "pkg.wakeword.demo",
            "--model-name",
            "Wakeword Demo",
            "--model-version",
            "0.1.0",
            "--model-description",
            "coverage gate packaging test",
            "--out",
            str(out),
        ]
    )
    pkg_payload = assert_json_success(pkg)
    assert Path(pkg_payload["manifest"]).is_file()

    validate = run_ef(["validate", "--efpkg", str(out)])
    validate_payload = assert_json_success(validate)
    assert validate_payload["ok"] is True


def _write_hub_package(pkg_dir: Path, *, name: str, model_id: str, version: str) -> None:
    manifest = {
        "schema_version": "0.1.0",
        "sdk_version": "0.1.0",
        "created_at": "2026-01-01T00:00:00Z",
        "model": {
            "id": model_id,
            "name": name,
            "version": version,
            "description": "hub cli roundtrip",
            "author": "alice",
            "domains": ["vision"],
            "tags": ["demo"],
        },
        "profile": {"name": "BASE"},
        "determinism": {
            "time_unit": "us",
            "mode": "fixed_step",
            "fixed_step_dt_us": 100,
            "epsilon_time_us": 100,
            "epsilon_numeric": 1e-5,
            "seed": 0,
        },
        "features": [],
        "capabilities_required": {},
        "artifacts": {
            "eir": {"path": "model.eir", "format": "json"},
            "traces": {"golden": {"path": "trace.jsonl", "format": "jsonl"}},
        },
        "compatibility": {},
    }
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (pkg_dir / "model.eir").write_text("{}", encoding="utf-8")
    (pkg_dir / "trace.jsonl").write_text('{"header":{"schema_version":"0.1.0"}}\n', encoding="utf-8")


@pytest.mark.e2e
def test_cli_hub_roundtrip_publish_list_info_search_install(tmp_path: Path) -> None:
    hub_root = tmp_path / "hub_root"
    pkg_dir = tmp_path / "pkg"
    install_dir = tmp_path / "installed"
    pkg_dir.mkdir()
    _write_hub_package(pkg_dir, name="vision-flow", model_id="pkg.vision.flow", version="1.0.0")

    publish = run_ef(
        [
            "hub",
            "--registry",
            str(hub_root),
            "publish",
            str(pkg_dir),
            "--username",
            "alice",
        ]
    )
    publish_payload = assert_json_success(publish)
    assert publish_payload["published"] == "vision-flow:1.0.0"

    listed = run_ef(["hub", "--registry", str(hub_root), "list"])
    listed_payload = assert_json_success(listed)
    assert any(p.get("name") == "vision-flow" for p in listed_payload["packages"])

    info = run_ef(["hub", "--registry", str(hub_root), "info", "vision-flow", "--version", "1.0.0"])
    info_payload = assert_json_success(info)
    assert info_payload["name"] == "vision-flow"
    assert info_payload["version"] == "1.0.0"

    search = run_ef(
        [
            "hub",
            "--registry",
            str(hub_root),
            "search",
            "vision",
            "--domain",
            "vision",
            "--author",
            "alice",
        ]
    )
    search_payload = assert_json_success(search)
    assert len(search_payload["packages"]) >= 1

    install = run_ef(
        [
            "hub",
            "--registry",
            str(hub_root),
            "install",
            "vision-flow",
            "--version",
            "1.0.0",
            "--dest",
            str(install_dir),
        ]
    )
    install_payload = assert_json_success(install)
    assert Path(install_payload["installed"]).is_dir()
    assert (Path(install_payload["installed"]) / "manifest.json").is_file()


@pytest.mark.e2e
def test_cli_hub_publish_requires_directory(tmp_path: Path) -> None:
    missing_path = tmp_path / "missing_pkg"
    proc = run_ef(["hub", "--registry", str(tmp_path / "hub"), "publish", str(missing_path)])
    payload = assert_json_error(proc, rc=2)
    assert "is not a directory" in payload["error"]


@pytest.mark.e2e
def test_cli_build_without_plan_out_returns_plan_json(repo_root: Path) -> None:
    eir = repo_root / "examples" / "vision_optical_flow" / "eir.json"
    proc = run_ef(["build", "--eir", str(eir), "--backend", "cpu-sim"])
    payload = parse_json_stdout(proc)
    assert proc.returncode == 0
    assert "backend" in payload
