# Contributing

Thank you for helping improve this research software repository. Contributions
should keep software behavior, simulation assumptions, biological assumptions,
and experimentally observed results clearly separated.

## Scope

This repository is a computational simulation project. Do not present simulation
outputs as direct evidence from real Drosophila, and do not introduce
Parkinson's disease validation, dopamine equivalence, disease-severity mapping,
biological rescue, or mechanistic claims without explicit project-owner
authorization and supporting evidence.

## Frozen Artifacts

Release v1.0.0, Milestones C-F, frozen evidence JSON, notebooks, manuscript
files, release artifacts, and release tags are frozen unless the project owner
explicitly authorizes a scoped change.

## Development Workflow

1. Open an issue or discussion for non-trivial changes.
2. Keep changes small and focused.
3. Prefer reusable code in `src/drosophila_pd/` and lightweight command-line
   entry points in `scripts/`.
4. Keep notebooks as research interfaces and historical records.
5. Do not rerun simulations, tune parameters, or modify evidence unless the
   task explicitly authorizes that work.
6. Run relevant checks before opening a pull request.

Recommended local checks:

```bash
python -m compileall -q src scripts tests
pytest -q -rs -p no:cacheprovider
git diff --check
```

## Pull Requests

Pull requests should describe:

- what changed;
- which files are intentionally touched;
- whether simulations were run;
- which evidence files, if any, were read or generated;
- what tests passed;
- any scientific-boundary risks.

Do not include large generated artifacts unless they are explicitly approved as
canonical evidence.
