from __future__ import annotations
import argparse
import sys
import os

def handle(ns):
    """Handle EventFlow Hub CLI commands.

    Provides commands for package management: publish, search, install, etc.

    Args:
        ns: Namespace object containing command-line arguments with attributes:
            subcommand: The hub subcommand (publish, search, install, etc.)
            Additional attributes depend on the subcommand.

    Returns:
        None: Exits with appropriate code instead of returning.

    Exit codes:
        0: Success
        1: Runtime error
        2: Argument/IO error
    """
    # Lazy import to avoid hard deps
    import os
    import sys
    # Add eventflow-hub to path for repo-local development
    hub_path = os.path.join(os.path.dirname(__file__), "..", "..", "eventflow-hub")
    if hub_path not in sys.path:
        sys.path.insert(0, hub_path)

    try:
        from eventflow_hub.client import HubClient
        from eventflow_hub.errors import HubError
    except ImportError as e:
        print(f"error: EventFlow Hub not available: {e}", file=sys.stderr)
        sys.exit(2)

    # Get global CLI_JSON
    json_output = getattr(sys.modules.get('__main__', None), 'CLI_JSON', False)

    # Hub registry root - can be overridden by env var
    hub_root = os.environ.get('EF_HUB_ROOT', './hub_registry')

    # Token for auth
    from eventflow_hub.auth import TokenProvider
    token_provider = TokenProvider()
    token = token_provider.get()

    # Create client - for v0.1, only local
    client = HubClient(root=hub_root, token=token)

    subcommand = getattr(ns, 'hub_subcommand', None)
    if not subcommand:
        print("error: no hub subcommand specified", file=sys.stderr)
        sys.exit(2)

    try:
        if subcommand == 'publish':
            _handle_publish(client, ns, json_output)
        elif subcommand == 'search':
            _handle_search(client, ns, json_output)
        elif subcommand == 'install':
            _handle_install(client, ns, json_output)
        elif subcommand == 'info':
            _handle_info(client, ns, json_output)
        elif subcommand == 'list':
            _handle_list(client, ns, json_output)
        else:
            print(f"error: unknown hub subcommand '{subcommand}'", file=sys.stderr)
            sys.exit(2)
    except HubError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"error: unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(0)


def _handle_publish(client: HubClient, ns, json_output: bool):
    package_path = ns.path
    username = ns.username or 'anonymous'

    if not os.path.isdir(package_path):
        print(f"error: package path '{package_path}' is not a directory", file=sys.stderr)
        sys.exit(2)

    key = client.publish_local(package_path, username)

    if json_output:
        import json
        print(json.dumps({"published": key}))
    else:
        print(f"Published {key}")


def _handle_search(client: HubClient, ns, json_output: bool):
    query = getattr(ns, 'query', '')
    domain = getattr(ns, 'domain', None)
    author = getattr(ns, 'author', None)

    results = client.search_local(query=query, domain=domain, author=author)

    if json_output:
        import json
        print(json.dumps({"packages": results}))
    else:
        if not results:
            print("No packages found")
            return

        print(f"Found {len(results)} package(s):")
        for pkg in results:
            print(f"  {pkg['name']}:{pkg['version']} - {pkg.get('description', 'No description')}")


def _handle_install(client: HubClient, ns, json_output: bool):
    name = ns.name
    version = getattr(ns, 'version', None)
    dest_dir = getattr(ns, 'dest', './packages')

    installed_path = client.install_local(name, version, dest_dir)

    if json_output:
        import json
        print(json.dumps({"installed": installed_path}))
    else:
        print(f"Installed to {installed_path}")


def _handle_info(client: HubClient, ns, json_output: bool):
    name = ns.name
    version = getattr(ns, 'version', None)

    info = client.get_local_package(name, version)
    if not info:
        print(f"error: package {name}:{version or 'latest'} not found", file=sys.stderr)
        sys.exit(1)

    if json_output:
        import json
        print(json.dumps(info))
    else:
        print(f"Package: {info['name']}:{info['version']}")
        print(f"Description: {info.get('description', 'N/A')}")
        print(f"Author: {info.get('author', 'N/A')}")
        print(f"Domains: {', '.join(info.get('domains', []))}")
        print(f"Size: {info.get('size_bytes', 0)} bytes")
        print(f"Uploaded: {info.get('uploaded_at', 'N/A')}")


def _handle_list(client: HubClient, ns, json_output: bool):
    packages = client.list_local()

    if json_output:
        import json
        print(json.dumps({"packages": packages}))
    else:
        if not packages:
            print("No packages in registry")
            return

        print(f"Registry contains {len(packages)} package(s):")
        for pkg in packages:
            print(f"  {pkg['name']}:{pkg['version']} - {pkg.get('description', 'No description')}")


# Subparser setup function for ef.py
def add_hub_subparser(hub_parser):
    """Add subcommands to the hub parser"""

    # Common hub arguments
    hub_parser.add_argument("--registry", default="./hub_registry",
                          help="Hub registry root directory (default: ./hub_registry)")

    # Sub-subcommands
    hub_sub = hub_parser.add_subparsers(dest="hub_subcommand", required=True)

    # publish
    pub = hub_sub.add_parser("publish", help="Publish a package to the hub")
    pub.add_argument("path", help="Path to package directory")
    pub.add_argument("--username", help="Publisher username (default: anonymous)")

    # search
    search = hub_sub.add_parser("search", help="Search packages in the hub")
    search.add_argument("query", nargs="?", default="", help="Search query")
    search.add_argument("--domain", help="Filter by domain")
    search.add_argument("--author", help="Filter by author")

    # install
    install = hub_sub.add_parser("install", help="Install a package from the hub")
    install.add_argument("name", help="Package name")
    install.add_argument("--version", help="Package version (default: latest)")
    install.add_argument("--dest", default="./packages", help="Destination directory")

    # info
    info = hub_sub.add_parser("info", help="Show package information")
    info.add_argument("name", help="Package name")
    info.add_argument("--version", help="Package version (default: latest)")

    # list
    hub_sub.add_parser("list", help="List all packages in the registry")

    return hub_parser