# Reproducibility Certificate

This certificate records the reproducibility audit for repository version
1.0.0.

## Environment And Evidence

Frozen upstream Colab evidence records:

- Python 3.12.13
- FlyGym 2.1.0
- MuJoCo 3.9.0

The final report package records:

- manuscript source: `docs/report/final_report.md`
- manuscript source commit:
  `004488cf7fd5e980137a209d360b977716865e1a`
- build implementation commit:
  `82746cf1276d3edf7e8ce3206d83f49b3470e1dd`
- PDF page count: 14
- final report artifact SHA-256 hashes in `dist/final_report_manifest.json`

## Artifact Hash Audit

The SHA-256 hashes and byte sizes for the version-controlled DOCX and PDF
matched `dist/final_report_manifest.json` during the final audit.

## Validation Commands

The final audit validation surface is:

```bash
python -m compileall -q src scripts tests
pytest -q -rs -p no:cacheprovider
git diff --check
```

The repository also has GitHub Actions for Continuous Integration and Markdown
Validation. Both workflows passed on the audit base commit.

## Reproduction Boundary

This certificate confirms repository and artifact reproducibility metadata. It
does not rerun FlyGym/MuJoCo simulations and does not upgrade the scientific
scope beyond the frozen evidence.
