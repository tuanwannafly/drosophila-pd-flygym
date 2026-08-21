# Reproducibility Statement

The repository is the source of truth for version-controlled code,
configuration, documentation, frozen evidence, and final report artifacts.
Google Colab is the recorded execution environment for upstream FlyGym and
MuJoCo simulation evidence.

The frozen simulation evidence reports Python 3.12.13, FlyGym 2.1.0, and
MuJoCo 3.9.0. The final report package is documented by
`dist/final_report_manifest.json`, which records artifact hashes, byte sizes,
PDF page count, manuscript source provenance, build provenance, and validation
results.

Repository validation commands:

```bash
python -m compileall -q src scripts tests
pytest -q -rs -p no:cacheprovider
git diff --check
```

The E6 synthesis can be regenerated from the frozen evidence package with:

```bash
python scripts/run_evidence_synthesis.py \
  --config configs/analysis/milestone_e6.yaml \
  --output results/analysis/milestone_e6_synthesis.json
```

Upstream simulation evidence should be reproduced only in the documented
FlyGym/MuJoCo environment and should not overwrite frozen v1.0.0 evidence
without an explicitly authorized new version.

This reproducibility statement covers computational and software
reproducibility only. It does not establish biological validation,
Parkinson's disease validation, dopamine equivalence, disease-severity mapping,
biological rescue, mechanistic equivalence, or statistical significance.
