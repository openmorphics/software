from __future__ import annotations
import json, os, shutil, hashlib
from typing import Dict, Optional, List, Any
from datetime import datetime

INDEX = "index.json"

class PackageRegistry:
    """
    Filesystem-based package registry for EventFlow packages.
    Stores packages as .efpkg directories or archives, with metadata index.
    """
    def __init__(self, root: str):
        self.root = root
        self.packages_dir = os.path.join(root, "packages")
        os.makedirs(self.packages_dir, exist_ok=True)
        self._index = self._load_index()

    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        index_path = os.path.join(self.root, INDEX)
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_index(self) -> None:
        index_path = os.path.join(self.root, INDEX)
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(self._index, f, indent=2, default=str)

    def _extract_metadata(self, manifest_path: str) -> Dict[str, Any]:
        """Extract package metadata from manifest"""
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        return {
            "id": manifest["model"]["id"],
            "name": manifest["model"]["name"],
            "version": manifest["model"]["version"],
            "description": manifest["model"].get("description", ""),
            "author": manifest["model"].get("author", ""),
            "tags": manifest["model"].get("tags", []),
            "domains": manifest["model"].get("domains", []),
            "sdk_version": manifest["sdk_version"],
            "created_at": manifest.get("created_at"),
            "uploaded_at": datetime.utcnow().isoformat() + "Z",
            "size_bytes": self._get_dir_size(os.path.dirname(manifest_path))
        }

    def _get_dir_size(self, path: str) -> int:
        total = 0
        for dirpath, _, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                total += os.path.getsize(filepath)
        return total

    def publish(self, package_path: str, username: str) -> str:
        """
        Publish a package directory to the registry.
        package_path should be a directory containing manifest.json or manifest.yaml
        """
        manifest_path = os.path.join(package_path, "manifest.json")
        if not os.path.isfile(manifest_path):
            manifest_path = os.path.join(package_path, "manifest.yaml")
            if not os.path.isfile(manifest_path):
                raise ValueError("Package must contain manifest.json or manifest.yaml")

        metadata = self._extract_metadata(manifest_path)
        name = metadata["name"]
        version = metadata["version"]

        # Create package directory
        pkg_dir = os.path.join(self.packages_dir, name, version)
        if os.path.exists(pkg_dir):
            raise ValueError(f"Package {name}:{version} already exists")

        os.makedirs(pkg_dir, exist_ok=True)

        # Copy package files
        for item in os.listdir(package_path):
            src = os.path.join(package_path, item)
            dst = os.path.join(pkg_dir, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        # Update index
        key = f"{name}:{version}"
        self._index[key] = {
            **metadata,
            "path": os.path.relpath(pkg_dir, self.root),
            "publisher": username
        }
        self._save_index()

        return key

    def get_package_info(self, name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get package metadata"""
        if version is None:
            # Get latest version
            candidates = [k for k in self._index.keys() if k.startswith(f"{name}:")]
            if not candidates:
                return None
            # Sort by version (simple string sort for now)
            key = sorted(candidates)[-1]
        else:
            key = f"{name}:{version}"

        return self._index.get(key)

    def get_package_path(self, name: str, version: Optional[str] = None) -> Optional[str]:
        """Get filesystem path to package"""
        info = self.get_package_info(name, version)
        if info:
            return os.path.join(self.root, info["path"])
        return None

    def search(self, query: str = "", domain: Optional[str] = None, author: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search packages by query, domain, author"""
        results = []
        for key, info in self._index.items():
            if query.lower() in info["name"].lower() or query.lower() in info["description"].lower():
                if domain and domain not in info.get("domains", []):
                    continue
                if author and info.get("author") != author:
                    continue
                results.append(info)
        return results

    def list_packages(self) -> List[Dict[str, Any]]:
        """List all packages"""
        return list(self._index.values())

    def delete_package(self, name: str, version: str, username: str) -> bool:
        """Delete a package (only by publisher)"""
        key = f"{name}:{version}"
        if key not in self._index:
            return False

        if self._index[key].get("publisher") != username:
            return False

        pkg_path = self.get_package_path(name, version)
        if pkg_path and os.path.exists(pkg_path):
            shutil.rmtree(pkg_path)

        del self._index[key]
        self._save_index()
        return True
