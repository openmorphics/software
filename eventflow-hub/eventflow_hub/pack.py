from __future__ import annotations
import os, tarfile
from typing import Optional
from .schemas import ModelCard, CapManifest, TraceMeta  # noqa: F401

def pack_bundle(src_dir: str, out_tar: str) -> str:
    """
    Bundle: model.eir, cap.json, trace.json, card.json → .tar.gz
    Returns path to created tar.gz.
    """
    required = ["model.eir","cap.json","trace.json","card.json"]
    for r in required:
        if not os.path.exists(os.path.join(src_dir, r)):
            raise FileNotFoundError(r)
    os.makedirs(os.path.dirname(out_tar) or ".", exist_ok=True)
    with tarfile.open(out_tar, "w:gz") as tar:
        for f in required:
            tar.add(os.path.join(src_dir, f), arcname=f)
    return out_tar

def unpack_bundle(tar_path: str, dest: str) -> str:
    os.makedirs(dest, exist_ok=True)
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(dest)
    return dest
