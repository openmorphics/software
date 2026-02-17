from __future__ import annotations
from typing import Optional, List, Dict, Any
from .registry import LocalRegistry, PackageRegistry
from .errors import HubError

class HubClient:
    """
    Unified client for EventFlow Hub operations.
    Supports local filesystem registry and remote HTTP (future).
    """
    def __init__(self, root: str = "./hub_registry", remote_url: Optional[str] = None, token: Optional[str] = None):
        self.local = PackageRegistry(root)
        self.remote_url = remote_url
        self.token = token

    # Local operations
    def publish_local(self, package_path: str, username: str) -> str:
        """Publish a package to local registry"""
        return self.local.publish(package_path, username)

    def get_local_package(self, name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get package info from local registry"""
        return self.local.get_package_info(name, version)

    def get_local_package_path(self, name: str, version: Optional[str] = None) -> Optional[str]:
        """Get package filesystem path from local registry"""
        return self.local.get_package_path(name, version)

    def search_local(self, query: str = "", domain: Optional[str] = None, author: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search packages in local registry"""
        return self.local.search(query=query, domain=domain, author=author)

    def list_local(self) -> List[Dict[str, Any]]:
        """List all packages in local registry"""
        return self.local.list_packages()

    def install_local(self, name: str, version: Optional[str] = None, dest_dir: str = "./packages") -> str:
        """Install package from local registry to dest_dir"""
        pkg_path = self.get_local_package_path(name, version)
        if not pkg_path:
            raise HubError(f"Package {name}:{version or 'latest'} not found in local registry")

        import os, shutil
        os.makedirs(dest_dir, exist_ok=True)
        dest_path = os.path.join(dest_dir, f"{name}-{version or 'latest'}")
        shutil.copytree(pkg_path, dest_path, dirs_exist_ok=True)
        return dest_path

    # Remote operations (not implemented in v0.1)
    def publish_remote(self, package_path: str) -> str:
        raise HubError("hub.remote_unsupported: remote hub not implemented in v0.1")

    def get_remote_package(self, name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        raise HubError("hub.remote_unsupported: remote hub not implemented in v0.1")

    def search_remote(self, query: str = "", domain: Optional[str] = None, author: Optional[str] = None) -> List[Dict[str, Any]]:
        raise HubError("hub.remote_unsupported: remote hub not implemented in v0.1")

    def install_remote(self, name: str, version: Optional[str] = None, dest_dir: str = "./packages") -> str:
        raise HubError("hub.remote_unsupported: remote hub not implemented in v0.1")
