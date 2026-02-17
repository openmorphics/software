from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any


def _emit_json(obj: dict[str, Any]) -> None:
    print(json.dumps(obj))


def _exit_error(message: str, exit_code: int, json_output: bool) -> None:
    if json_output:
        _emit_json({"ok": False, "error": message})
    else:
        print(f"error: {message}", file=sys.stderr)
    sys.exit(exit_code)


def handle(ns, json_output: bool = False):
    """Handle EventFlow Hub CLI commands."""
    # Lazy import to avoid hard deps.
    hub_path = os.path.join(os.path.dirname(__file__), "..", "..", "eventflow-hub")
    if hub_path not in sys.path:
        sys.path.insert(0, hub_path)

    try:
        from eventflow_hub.client import HubClient
        from eventflow_hub.errors import HubError
    except ImportError as e:
        _exit_error(f"EventFlow Hub not available: {e}", 2, json_output)

    # Priority: --registry > EF_HUB_ROOT > default.
    hub_root = getattr(ns, "registry", None) or os.environ.get("EF_HUB_ROOT") or "./hub_registry"

    from eventflow_hub.auth import TokenProvider

    token_provider = TokenProvider()
    token = token_provider.get()
    client = HubClient(root=hub_root, token=token)

    subcommand = getattr(ns, "hub_subcommand", None)
    if not subcommand:
        _exit_error("no hub subcommand specified", 2, json_output)

    try:
        if subcommand == "publish":
            _handle_publish(client, ns, json_output)
        elif subcommand == "search":
            _handle_search(client, ns, json_output)
        elif subcommand == "install":
            _handle_install(client, ns, json_output)
        elif subcommand == "info":
            _handle_info(client, ns, json_output)
        elif subcommand == "list":
            _handle_list(client, ns, json_output)
        else:
            _exit_error(f"unknown hub subcommand '{subcommand}'", 2, json_output)
    except HubError as e:
        _exit_error(str(e), 1, json_output)
    except Exception as e:
        _exit_error(f"unexpected error: {e}", 1, json_output)

    sys.exit(0)


def _handle_publish(client: Any, ns, json_output: bool) -> None:
    package_path = ns.path
    username = ns.username or "anonymous"

    if not os.path.isdir(package_path):
        _exit_error(f"package path '{package_path}' is not a directory", 2, json_output)

    key = client.publish_local(package_path, username)
    if json_output:
        _emit_json({"published": key})
    else:
        print(f"Published {key}")


def _handle_search(client: Any, ns, json_output: bool) -> None:
    query = getattr(ns, "query", "")
    domain = getattr(ns, "domain", None)
    author = getattr(ns, "author", None)

    results = client.search_local(query=query, domain=domain, author=author)
    if json_output:
        _emit_json({"packages": results})
    else:
        if not results:
            print("No packages found")
            return
        print(f"Found {len(results)} package(s):")
        for pkg in results:
            print(f"  {pkg['name']}:{pkg['version']} - {pkg.get('description', 'No description')}")


def _handle_install(client: Any, ns, json_output: bool) -> None:
    name = ns.name
    version = getattr(ns, "version", None)
    dest_dir = getattr(ns, "dest", "./packages")

    installed_path = client.install_local(name, version, dest_dir)
    if json_output:
        _emit_json({"installed": installed_path})
    else:
        print(f"Installed to {installed_path}")


def _handle_info(client: Any, ns, json_output: bool) -> None:
    name = ns.name
    version = getattr(ns, "version", None)

    info = client.get_local_package(name, version)
    if not info:
        _exit_error(f"package {name}:{version or 'latest'} not found", 1, json_output)

    if json_output:
        _emit_json(info)
    else:
        print(f"Package: {info['name']}:{info['version']}")
        print(f"Description: {info.get('description', 'N/A')}")
        print(f"Author: {info.get('author', 'N/A')}")
        print(f"Domains: {', '.join(info.get('domains', []))}")
        print(f"Size: {info.get('size_bytes', 0)} bytes")
        print(f"Uploaded: {info.get('uploaded_at', 'N/A')}")


def _handle_list(client: Any, ns, json_output: bool) -> None:
    packages = client.list_local()

    if json_output:
        _emit_json({"packages": packages})
    else:
        if not packages:
            print("No packages in registry")
            return
        print(f"Registry contains {len(packages)} package(s):")
        for pkg in packages:
            print(f"  {pkg['name']}:{pkg['version']} - {pkg.get('description', 'No description')}")


def add_hub_subparser(hub_parser: argparse.ArgumentParser):
    """Add subcommands to the hub parser."""
    hub_parser.add_argument(
        "--registry",
        default=None,
        help="Hub registry root directory (overrides EF_HUB_ROOT; default: ./hub_registry)",
    )

    hub_sub = hub_parser.add_subparsers(dest="hub_subcommand", required=True)

    pub = hub_sub.add_parser("publish", help="Publish a package to the hub")
    pub.add_argument("path", help="Path to package directory")
    pub.add_argument("--username", help="Publisher username (default: anonymous)")

    search = hub_sub.add_parser("search", help="Search packages in the hub")
    search.add_argument("query", nargs="?", default="", help="Search query")
    search.add_argument("--domain", help="Filter by domain")
    search.add_argument("--author", help="Filter by author")

    install = hub_sub.add_parser("install", help="Install a package from the hub")
    install.add_argument("name", help="Package name")
    install.add_argument("--version", help="Package version (default: latest)")
    install.add_argument("--dest", default="./packages", help="Destination directory")

    info = hub_sub.add_parser("info", help="Show package information")
    info.add_argument("name", help="Package name")
    info.add_argument("--version", help="Package version (default: latest)")

    hub_sub.add_parser("list", help="List all packages in the registry")
    return hub_parser
