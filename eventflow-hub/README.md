# EventFlow Hub

`eventflow-hub` is a local artifact registry and bundle packager for EventFlow packages.

## Current State

- Working today: local registry metadata, bundle packaging helpers, schemas, and local client/registry tests.
- Not implemented: remote push, pull, publish, and fetch operations. The code intentionally raises `hub.remote_unsupported` for remote methods in this version.
- This package is not a hosted service and does not provide cloud storage or authentication flows beyond local scaffolding.

## Local Usage

Use through the CLI after editable installation:

```bash
python eventflow-cli/ef.py --json hub --help
```

Use package APIs for local registry and package operations:

```python
from eventflow_hub.registry import LocalRegistry
from eventflow_hub.pack import pack_bundle
```

## Testing

```bash
python -m pytest -q eventflow-hub/tests tests/unit/test_hub_registry_client_extra.py -rs
```
