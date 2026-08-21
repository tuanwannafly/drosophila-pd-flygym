# Project Health

This report is a repository-maintenance snapshot, not a scientific result.
It reflects the checked-in tree at the migration checkpoint.

## Inventory

| Category | Count or state |
| --- | ---: |
| Python source files under `src/` | 187 |
| Named Python subpackage areas | 16 top-level, plus `flystudio.integration` |
| CLI scripts under `scripts/` | 25 |
| Configuration files under `configs/` | 16 |
| Python test files under `tests/` | 40 |
| Evidence JSON reports under `results/` | 11 |
| Frozen E6 figures | 4 |
| Frozen E6 tables | 5 |
| Historical notebooks | 2 |
| Markdown files under `docs/` | 332 before this migration package |
| Release tag | `v1.0.0` |
| Current branch at snapshot | `main` |

Counts exclude ignored Python cache directories and are intended for orientation
rather than a contractual build output.

## Health signals

The existing release-candidate health report records:

- no local Python dependency cycles;
- all required release modules present;
- configuration consistency checked for 13 non-empty configuration files;
- plugin examples with a manifest and run boundary;
- informational duplicate module names and unused export/import findings.

The informational findings are retained as technical-debt observations. This
migration does not refactor scientific or V2 implementation modules.

## Architecture maturity

The scientific V1 path is mature enough to be frozen and reproduced with the
documented FlyGym/MuJoCo environment. The V2 platform is additive and broad,
with unit/integration coverage and module-specific documentation, but its
interfaces should be treated as evolving until a future release explicitly
freezes them.

## Research maturity

The repository contains frozen computational evidence through Milestone E6 and
a frozen publication package. The evidence supports software reproducibility
and qualitative endpoint concordance only. It does not establish biological
Parkinson's disease validation.

## Technical debt

- Several V2 areas intentionally expose similar concepts for different layers
  (for example comparison, gait, open-field, statistics, report, and viewer).
- Release-candidate analysis reports informational duplicate names and unused
  exports/imports.
- Large/raw rollout and video artifacts are intentionally not part of the
  version-controlled release.
- The historical Session 02 notebook is a research record and is not a package
  API.

## Maintenance rule

Prefer documentation, tests, and compatibility-preserving adapters before
refactoring broad platform areas. Any scientific change requires separate
authorization and evidence review.
