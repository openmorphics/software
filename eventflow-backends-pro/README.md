# EventFlow Pro Backends

`eventflow-backends-pro` contains proprietary vendor adapter scaffolding for neuromorphic hardware targets.

## Current State

- Included adapter families: Loihi, SpiNNaker, and SynSense.
- The package exposes entry points and backend-shaped modules for integration work.
- Actual hardware execution is not guaranteed by this repository. It depends on vendor SDK availability, real hardware access, matching runtime configuration, and a valid license.
- When vendor SDKs or hardware are absent, adapters can run in stub mode and report that no real hardware execution occurred.

## Licensing

This is a proprietary package. Use it only in environments where the relevant EventFlow Pro or Enterprise license and vendor SDK terms are satisfied.

The CLI may gate Pro features through `eventflow-license`; this package does not by itself provide certification or hardware access.

## Local Development

From the repository root:

```bash
python -m pip install -e ./eventflow-license -e ./eventflow-core -e ./eventflow-backends
python -m pip install -e ./eventflow-backends-pro
```

## Testing

```bash
python -m pytest -q eventflow-backends/tests/test_loihi.py eventflow-backends/tests/test_spinnaker.py eventflow-backends/tests/test_synsense.py -rs
```

Those tests validate adapter shape and error contracts. They do not prove live hardware execution.
