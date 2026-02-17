from __future__ import annotations

import json
from pathlib import Path

import pytest

from eventflow_hub.client import HubClient
from eventflow_hub.errors import HubError
from eventflow_hub.registry import LocalRegistry, PackageRegistry


def _write_manifest(pkg_dir: Path, *, name: str, model_id: str, version: str, author: str = "alice") -> Path:
    manifest = {
        "schema_version": "0.1.0",
        "sdk_version": "0.1.0",
        "created_at": "2026-01-01T00:00:00Z",
        "model": {
            "id": model_id,
            "name": name,
            "version": version,
            "description": "test package",
            "author": author,
            "domains": ["vision"],
            "tags": ["test"],
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
    manifest_path = pkg_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    (pkg_dir / "model.eir").write_text("{}", encoding="utf-8")
    (pkg_dir / "trace.jsonl").write_text('{"header":{"schema_version":"0.1.0"}}\n', encoding="utf-8")
    return manifest_path


def test_package_registry_publish_search_delete(tmp_path: Path) -> None:
    registry_root = tmp_path / "registry"
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir()
    _write_manifest(pkg_dir, name="vision-flow", model_id="pkg.vision.flow", version="1.0.0", author="alice")

    registry = PackageRegistry(str(registry_root))
    key = registry.publish(str(pkg_dir), "alice")
    assert key == "vision-flow:1.0.0"

    info = registry.get_package_info("vision-flow", "1.0.0")
    assert info is not None
    assert info["publisher"] == "alice"
    assert info["author"] == "alice"

    latest = registry.get_package_info("vision-flow")
    assert latest is not None
    assert latest["version"] == "1.0.0"

    search = registry.search(query="vision", domain="vision", author="alice")
    assert len(search) == 1
    assert search[0]["name"] == "vision-flow"

    # Wrong user cannot delete.
    assert registry.delete_package("vision-flow", "1.0.0", "bob") is False
    assert registry.delete_package("vision-flow", "1.0.0", "alice") is True
    assert registry.get_package_info("vision-flow", "1.0.0") is None


def test_hub_client_local_install_and_remote_errors(tmp_path: Path) -> None:
    root = tmp_path / "hub"
    pkg_dir = tmp_path / "pkg"
    install_dir = tmp_path / "installed"
    pkg_dir.mkdir()
    _write_manifest(pkg_dir, name="audio-kws", model_id="pkg.audio.kws", version="0.1.0")

    client = HubClient(root=str(root))
    key = client.publish_local(str(pkg_dir), "alice")
    assert key == "audio-kws:0.1.0"

    info = client.get_local_package("audio-kws", "0.1.0")
    assert info is not None
    assert info["name"] == "audio-kws"

    installed = client.install_local("audio-kws", "0.1.0", dest_dir=str(install_dir))
    assert Path(installed).is_dir()
    assert (Path(installed) / "manifest.json").is_file()

    with pytest.raises(HubError, match="remote hub not implemented"):
        client.publish_remote(str(pkg_dir))
    with pytest.raises(HubError, match="remote hub not implemented"):
        client.get_remote_package("audio-kws", "0.1.0")
    with pytest.raises(HubError, match="remote hub not implemented"):
        client.search_remote("audio")
    with pytest.raises(HubError, match="remote hub not implemented"):
        client.install_remote("audio-kws", "0.1.0")


def test_local_registry_duplicate_and_missing_bundle_errors(tmp_path: Path) -> None:
    reg = LocalRegistry(str(tmp_path / "local_reg"))
    missing = tmp_path / "missing.tar.gz"

    with pytest.raises(FileNotFoundError):
        reg.add("demo", "1.0.0", str(missing))

    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"dummy")
    key = reg.add("demo", "1.0.0", str(bundle))
    assert key == "demo:1.0.0"
    assert reg.get("demo", "1.0.0") is not None

    with pytest.raises(ValueError, match="already exists"):
        reg.add("demo", "1.0.0", str(bundle))
