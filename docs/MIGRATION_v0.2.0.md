# Migration Guide: v0.1.0 to v0.2.0 (Open Core Reseal)

EventFlow v0.2.0 introduces an "Open Core" model, separating baseline simulator support from production-grade features.

## Major Changes

1.  **Package Reseal**: Vendor-specific backends and industrial domain modules have moved to the **EventFlow Pro** index.
2.  **Versioning**: All packages have been bumped to `0.2.0`. Mixed-version installs (e.g., core 0.1.0 with CLI 0.2.0) are not supported.
3.  **Licensing**: Production features now require an offline license token.

## Upgrade Path

### 1. Update Public Packages
Baseline packages remain on public PyPI.

```bash
pip install --upgrade eventflow-cli eventflow-core eventflow-modules
```

### 2. Access Pro Features (Licensed Users)
If you require hardware backends (Loihi, SpiNNaker, SynSense) or Conformance verification:

1.  Add the EventFlow private index:
    ```bash
    pip install eventflow-conformance eventflow-backends-pro \
        --extra-index-url https://pypi.eventflow.dev/YOUR_TOKEN/
    ```
2.  Install your license:
    ```bash
    eventflow license install ./path/to/license.json
    ```

## Feature Mapping

| Feature | v0.1.0 Package | v0.2.0 Package | Tier |
| :--- | :--- | :--- | :--- |
| CPU/GPU Sim | `eventflow-backends` | `eventflow-backends` | Community |
| Hardware Adapters | `eventflow-backends` | `eventflow-backends-pro` | Pro |
| Basic Modules | `eventflow-modules` | `eventflow-modules` | Community |
| Industrial Modules | `eventflow-modules` | `eventflow-modules-pro` | Pro (Roadmap) |
| Conformance | `eventflow-core` | `eventflow-conformance` | Pro |
