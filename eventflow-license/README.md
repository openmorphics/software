# EventFlow License

This package provides license validation and management for the EventFlow SDK.

## License Structure

EventFlow uses signed JSON license files (Ed25519) that contain:
- Entitled features
- Expiration date
- Organization name
- Cryptographic signature

## Usage

```python
from eventflow_license import LicenseValidator

validator = LicenseValidator()
if validator.check("conformance"):
    print("Conformance features enabled")
```
