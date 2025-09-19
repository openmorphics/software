from __future__ import annotations
import json, os
from typing import Dict, Optional, List

INDEX = "index.json"

class LocalRegistry:
    """
    Minimal filesystem registry: one directory; index.json maps name:version → files.
    """
    def __init__(self, root: str):
        self.root = root
        os.makedirs(root, exist_ok=True)
        self._index = self._load()

    def _load(self) -> Dict[str, Dict]:
        path = os.path.join(self.root, INDEX)
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
        return {}

    def _save(self) -> None:
        with open(os.path.join(self.root, INDEX), "w") as f:
            json.dump(self._index, f, indent=2)

    def add(self, name: str, version: str, bundle_path: str) -> str:
        key = f"{name}:{version}"
        dest = os.path.join(self.root, f"{name}-{version}.tar.gz")
        os.replace(bundle_path, dest)
        self._index[key] = {"bundle": os.path.basename(dest)}
        self._save()
        return key

    def get(self, name: str, version: Optional[str]=None) -> Optional[str]:
        if version is None:
            candidates = sorted([k for k in self._index if k.startswith(name + ":")])
            if not candidates:
                return None
            version = candidates[-1].split(":",1)[1]
        key = f"{name}:{version}"
        rec = self._index.get(key)
        return os.path.join(self.root, rec["bundle"]) if rec else None

    def list(self) -> List[str]:
        return sorted(self._index.keys())
