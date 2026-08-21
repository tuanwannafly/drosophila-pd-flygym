# Regression Review

## Protected paths

No changes were made to `src/`, `configs/`, `results/`, `dist/`, `notebooks/`,
`docs/report/`, or `web/`. The changes are limited to documentation, metadata,
research-directory anchors, templates, and GitHub review checklists.

## Validation

- `python -m compileall -q src scripts tests`: passed.
- `pytest -q -rs -p no:cacheprovider`: 300 passed, 3 expected Colab integration
  skips.
- `git diff --check`: passed.
- Repository Markdown formatting validation: passed.
- Local Markdown-link check: passed.
- JSON parsing for `codemeta.json` and the dependency manifest: passed.

No FlyGym/MuJoCo simulation or notebook was executed.
