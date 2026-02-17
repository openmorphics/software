# Licensing and Tiers

EventFlow v0.2.0 uses a tiered distribution model to balance rapid community adoption with enterprise-grade reliability.

## Tiers

### Community (Free)
- **Included**: `eventflow-core`, `eventflow-sal`, `eventflow-backends` (Sim), `eventflow-cli`, `eventflow-modules` (subset).
- **Target**: Researchers, hobbyists, and initial technical evaluation.
- **License**: BSD-3-Clause.

### Pro (Paid)
- **Included**: Everything in Community + `eventflow-backends-pro`, `eventflow-conformance`.
- **Target**: Production deployment on hardware, regulated industries.
- **Licensing**: Proprietary EULA.

## License Management

EventFlow uses signed JSON license files for offline validation.

### Installation
```bash
eventflow license install my-license.json
```

### Checking Status
```bash
eventflow license status
```

## Commercial Features

### 1. Certified Backends
Access to specialized neuromorphic hardware (Intel Loihi, SpiNNaker, SynSense) is gated via `eventflow-backends-pro`.

### 2. Conformance & Evidence
Generate audit-grade evidence reports for regulatory compliance (Automotive, Medical).
```bash
eventflow verify-conformance --eir model.json --cert-profile AUTOMOTIVE_ISO26262
```
