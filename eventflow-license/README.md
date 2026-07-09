# EventFlow License

`eventflow-license` provides signed-license validation utilities used by the CLI and Pro-facing packages.

## Current State

- Working today: Ed25519-style signed JSON license validation, cache helpers, and typed license errors.
- Used by: `eventflow-cli`, `eventflow-backends-pro`, and `eventflow-conformance`.
- Scope boundary: this package validates local license material. It does not provide a license server, billing system, customer portal, or legal entitlement process.

## License Structure

License files contain:

- entitled features
- expiration date
- organization name
- cryptographic signature

## Usage

```python
from eventflow_license import LicenseError, LicenseValidator

validator = LicenseValidator()
try:
    validator.require("conformance")
except LicenseError as exc:
    print(f"feature unavailable: {exc}")
```

## Testing

```bash
python -m pytest -q eventflow-license/tests -rs
```
