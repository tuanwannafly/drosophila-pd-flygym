# Repository Certification

This certificate records the final v1 audit of the frozen repository. It is an
audit document only. It does not modify source code, simulations,
perturbations, evidence, manuscript content, release artifacts, notebooks, or
scientific conclusions.

## Certification Result

Repository version 1.0.0 is certified as structurally complete for public
dissemination and long-term archival, subject to the scientific boundary stated
in `docs/final_audit/scientific_scope.md`.

## Verified Repository Components

| Component | Status | Evidence |
| --- | --- | --- |
| Repository structure | PASS | `src/`, `scripts/`, `configs/`, `tests/`, `docs/`, `results/`, `dist/` |
| Milestones | PASS | Project context, frozen evidence JSON, report traceability |
| Release artifacts | PASS | `dist/Drosophila_PD_FlyGym_Final_Report.docx`, PDF, manifest |
| Evidence packages | PASS | 11 JSON reports under `results/` |
| Manuscript | PASS | `docs/report/final_report.md` |
| Report package | PASS | `docs/report/` and `dist/` |
| Publication package | PASS | `docs/publication/` and `docs/publication_checklist.md` |
| Journal submission package | PASS | `docs/submission/` |
| Archive package | PASS | `docs/archive/` |
| GitHub workflows | PASS | `.github/workflows/ci.yml`, `.github/workflows/markdown.yml` |
| License | PASS | `LICENSE` |
| Citation metadata | PASS | `CITATION.cff`, `docs/citation.md` |
| Release notes | PASS | `docs/release/v1.0.0.md` |
| Community files | PASS | `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md` |
| README | PASS | `README.md` |
| Release tag | PASS | `v1.0.0` resolves to `260f858628d49032e7487f831bf509f93fc7ed29` |
| Release manifest | PASS | `dist/final_report_manifest.json` |

## Commit Provenance

- Audit base HEAD: `f921eb44d12a8021008e18337461fb7b0c5c5c15`
- Release tag `v1.0.0`: `260f858628d49032e7487f831bf509f93fc7ed29`
- Manuscript source commit:
  `004488cf7fd5e980137a209d360b977716865e1a`
- Final report build implementation commit:
  `82746cf1276d3edf7e8ce3206d83f49b3470e1dd`
- E6 evidence synthesis implementation commit:
  `53e41d17365f56509ca708ba3352ddf724b0e89a`

The release tag preserves the release snapshot. The canonical `main` branch
contains the frozen release state plus subsequent public dissemination,
submission, archival, and certification documentation.
