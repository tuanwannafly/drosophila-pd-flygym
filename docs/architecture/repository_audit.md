# Repository Audit

Audit date: 2026-08-15

Audit basis: repository `main` at `7a9ce20`. The working tree already had
three user edits in `notebooks/colab/00_Environment_Setup.ipynb`,
`01_FlyGym_API_Explorer.ipynb`, and `02_Create_First_Fly.ipynb`; those files
are explicitly outside this audit change and were not modified.

This is a maintenance audit. It does not change scientific code, evidence,
manuscript content, notebooks, or release artifacts.

## Inventory

Counts below exclude `.git` internals and Python `__pycache__` directories.

| Area | Files | Role | Classification |
| --- | ---: | --- | --- |
| `src/` | 241 | Importable package and package data | KEEP |
| `scripts/` | 30 | Explicit command-line boundaries | KEEP |
| `tests/` | 121 | Regression and contract tests | KEEP |
| `configs/` | 29 | Experiment and platform configuration | KEEP |
| `web/` | 74 | Browser viewer and research workspace | KEEP |
| `docs/` | 582 | Scientific, release, V2, and developer documentation | KEEP/REVIEW_REQUIRED |
| `notebooks/` | 22 | Historical and Colab research interfaces | KEEP |
| `results/` | 45 | Curated evidence and generated summaries | KEEP/FROZEN |
| `dist/` | 17 | Frozen report package and supporting assets | KEEP/FROZEN |

The source count includes package data and the package root. The committed
release and evidence files remain authoritative even when a newer planning
document exists elsewhere in the tree.

## Dependency Map

```text
configs -> scripts -> experiments/controllers/perturbations -> results
imported rollout -> metrics/assays/behavior_platform -> reports/figures/tables
existing artifacts -> research_execution/research_campaign/research_pipeline
frozen evidence -> analysis/evidence_synthesis -> E6 figures/tables -> report
viewer_pose.json -> web/viewer/* -> future Digital Laboratory UI
```

The existing release-candidate dependency report found no local Python import
cycles. The browser application is an ES-module graph rooted at
`web/main.js`; the new `web/viewer/` directory is an additive, currently
standalone layer and is not wired into the existing application in this phase.

## Duplicate Names

Duplicate basenames are not proof of duplicate implementation. Confirmed
overlap names include `comparison`, `gait`, `healthy_baseline`, `open_field`,
`report`, `statistics`, `turning`, `validation`, `viewer`, and
`visualization`. They belong to different contracts: scientific metrics,
assays, computational-PD reporting, validation, Python Fly Studio, or browser
presentation. They are therefore classified `REVIEW_REQUIRED`, not deleted.

The release-candidate health report also records informational unused-export
and unused-import findings. Those are static-analysis candidates, not proof of
dead runtime behavior. No source refactor is made without a call-site and
public-API review.

## Documentation Duplication

`docs/v2/` contains module-specific architecture, API, tutorial, limitation,
and regression documents. Similar filenames such as `README.md`, `api.md`,
and `architecture.md` are scoped to their directory. `docs/v4/` through
`docs/v10/`, `docs/archive/`, `docs/submission/`, and `docs/final_audit/`
record distinct workflow or release checkpoints. They are kept because
cross-links, provenance, and historical reproducibility depend on them.

The new [documentation index](../README.md) is the preferred navigation layer;
it does not replace the scoped documents.

## Classification

| Candidate | Status | Reason |
| --- | --- | --- |
| `.git` and ignored Python caches | SAFE_TO_DELETE | Generated VCS/build state; not repository content |
| `results/kernel/` when empty | SAFE_TO_DELETE | Empty operational output anchor; no tracked artifact |
| Frozen `results/` JSON/CSV/PNG | KEEP | Evidence and E6 provenance are frozen |
| `dist/` report deliverables | KEEP | Release v1.0.0 artifacts |
| `notebooks/` | KEEP | Historical research records; Session 02 is protected |
| `docs/release_candidate/` | KEEP | Release health, API, and provenance inventory |
| `docs/v2/`, `docs/v4/`–`docs/v10/` | REVIEW_REQUIRED | Scoped historical and platform documentation |
| Similar Python module basenames | REVIEW_REQUIRED | Semantic overlap is not established |
| Static unused-import/export findings | REVIEW_REQUIRED | Existing heuristic can produce false positives |
| Web modules not imported by `web/main.js` | REVIEW_REQUIRED | Some are public integration or future UI surfaces |

No files are deleted or moved by this audit. Items marked
`SAFE_TO_ARCHIVE` in the archive manifest require a future call-site review
before relocation.

## Technical Debt

- Many V2 layers expose intentionally similar concepts at different boundaries.
- Documentation has grown by milestone and therefore needs index-driven
  navigation rather than broad merges.
- The browser workspace has a mature existing surface but no single stable
  pose interchange contract; this phase adds that contract without wiring it
  into scientific code.
- Coverage is not measured by the release builder; pytest remains the current
  regression gate.

## Decision

The safe rationalization action for this phase is documentation and boundary
clarification. No scientific implementation, evidence, notebook, or release
artifact is changed, and no duplicate module is removed without stronger
repository-supported proof.
