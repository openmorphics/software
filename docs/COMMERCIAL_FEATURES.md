# Conformance Verification (Pro Feature)

The Conformance Verification suite provides deep static and dynamic analysis of EIR graphs to ensure they meet strict operational requirements for safety-critical environments.

## Evidence Reports

The `verify-conformance` command generates detailed JSON evidence reports. These reports link the graph state (via SHA256 hashes) to verification results, providing a chain of custody for regulatory audits.

### Key Evidence Fields:
- `eir_sha256`: Unique fingerprint of the model.
- `profile`: The certification standard applied (e.g., ISO 26262).
- `violations`: Exhaustive list of non-compliance issues.
- `status`: Binary PASSED/FAILED result.

## Profiles

| Profile | Target Industry | Key Constraints |
| :--- | :--- | :--- |
| `BASE` | General | Basic determinism check. |
| `AUTOMOTIVE_ISO26262` | Automotive | <10ms latency, redundancy, hardware parity. |
| `MEDICAL_IEC62304` | Medical | <50ms latency, strict audit logging. |

## Usage

```bash
eventflow verify-conformance \
    --eir my_model.eir.json \
    --cert-profile AUTOMOTIVE_ISO26262 \
    --evidence-out report.json
```
