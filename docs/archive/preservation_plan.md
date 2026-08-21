# Preservation Plan

This preservation plan documents how to keep repository version 1.0.0 usable
for future readers.

## Preserve

- Git commit history and Release `v1.0.0`.
- `LICENSE`, `CITATION.cff`, and `docs/citation.md`.
- Final report artifacts and `dist/final_report_manifest.json`.
- Frozen evidence JSON files under `results/`.
- E6 figures and CSV tables under `results/analysis/`.
- Report, publication, submission, archive, and traceability documentation.
- Source, configuration, scripts, and tests needed to inspect or reproduce the
  computational workflow.

## Verify

Before archival, run:

```bash
python -m compileall -q src scripts tests
pytest -q -rs -p no:cacheprovider
git diff --check
```

Also verify that report artifacts, citation files, license, community files,
publication package, submission package, and evidence inventory paths resolve.

## Future Updates

Future work should not overwrite frozen v1.0.0 evidence or artifacts. New
scientific or software work should create a new versioned evidence package and
release.
