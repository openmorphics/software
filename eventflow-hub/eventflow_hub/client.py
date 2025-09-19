from __future__ import annotations
from typing import Optional, List
from .registry import LocalRegistry
from .errors import HubError

class HubClient:
    """
    Unified client: local filesystem (default) or remote HTTP (future).
    """
    def __init__(self, root: str, remote_url: Optional[str]=None, token: Optional[str]=None):
        self.local = LocalRegistry(root)
        self.remote_url = remote_url
        self.token = token

    # Local
    def push_local(self, name: str, version: str, bundle_path: str) -> str:
        return self.local.add(name, version, bundle_path)

    def pull_local(self, name: str, version: Optional[str]=None) -> Optional[str]:
        return self.local.get(name, version)

    def list_local(self) -> List[str]:
        return self.local.list()

    # Remote (not implemented in v0.1)
    def push_remote(self, name: str, version: str, bundle_path: str) -> str:
        raise HubError("hub.remote_unsupported: remote hub not implemented")

    def pull_remote(self, name: str, version: Optional[str]=None) -> Optional[str]:
        raise HubError("hub.remote_unsupported: remote hub not implemented")
