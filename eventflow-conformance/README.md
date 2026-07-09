# EventFlow Conformance

`eventflow-conformance` is a proprietary package for conformance profiles, validators, and evidence-export scaffolding.

## Current State

- Working today: profile/evidence/validator modules with package-level tests and integration points.
- Scope boundary: this is not a complete regulatory certification system. It does not by itself certify a product, hardware deployment, or safety case.
- License dependency: Pro conformance features depend on `eventflow-license`.
- Baseline trace comparison also exists in `eventflow-core`; this package is for Pro-facing conformance/evidence workflows.

## Intended Use

- Define certification-oriented validation profiles.
- Collect deterministic evidence artifacts from EventFlow runs.
- Add stricter validation around determinism, latency, and resource constraints.

Treat generated evidence as engineering evidence unless a separate audit/certification process accepts it.

## Local Development

```bash
python -m pip install -e ./eventflow-core -e ./eventflow-license -e ./eventflow-conformance
```

## Testing

```bash
python -m pytest -q tests/conformance -rs
```
