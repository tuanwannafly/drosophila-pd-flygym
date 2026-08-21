# Release Engineering

This directory contains additive developer/release tooling for V2. It is
separate from the frozen V1 manuscript and final report artifacts under
`dist/`.

## Outputs

- `release.json`: machine-readable release manifest and health summary.
- `release.md`: human-readable release report.
- `release.html`: lightweight HTML report.

Regenerate with:

```bash
PYTHONPATH=src python scripts/generate_release_report.py
```

The generator inventories source files and static contracts. It does not run
FlyGym, MuJoCo, simulations, or evidence-producing experiments.
