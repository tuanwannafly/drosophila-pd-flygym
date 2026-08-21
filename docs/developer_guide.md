# Developer Guide

Reusable logic belongs in `src/drosophila_pd/`; scripts should remain thin
command-line boundaries. Tests belong in `tests/`, and new documentation should
state whether it describes frozen science, imported-artifact analysis, or
workflow tooling.

Before a pull request, run the checks in
`.github/workflows/ci.yml` and `.github/workflows/markdown.yml`. Do not modify
frozen evidence, the manuscript, release artifacts, or historical notebooks
without explicit scope.

See [CONTRIBUTING.md](../CONTRIBUTING.md) and the [public API](public_api.md).
