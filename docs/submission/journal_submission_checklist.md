# Journal Submission Checklist

This checklist is for preparing a journal submission from the frozen v1.0.0
repository. It must not be used to change scientific results, frozen evidence,
simulation code, notebooks, manuscript conclusions, or release artifacts.

## Manuscript Files

- [ ] Use `dist/Drosophila_PD_FlyGym_Final_Report.pdf` as the formatted PDF.
- [ ] Use `dist/Drosophila_PD_FlyGym_Final_Report.docx` when a DOCX upload is
      required.
- [ ] Preserve `docs/report/final_report.md` as the canonical manuscript
      source.
- [ ] Confirm `dist/final_report_manifest.json` records the final artifact
      hashes and provenance.

## Supplementary Files

- [ ] Include frozen evidence JSON files from `results/`.
- [ ] Include E6 figures from `results/analysis/figures/`.
- [ ] Include E6 CSV tables from `results/analysis/tables/`.
- [ ] Include release notes from `docs/release/v1.0.0.md`.
- [ ] Include citation metadata from `CITATION.cff` and `docs/citation.md`.
- [ ] Include the MIT license from `LICENSE`.

## Scientific Boundary

- [ ] Preserve the computational/phenomenological scope.
- [ ] Preserve `PARTIAL_PHENOTYPE_CONCORDANCE` as qualitative only.
- [ ] Do not add Parkinson's disease validation claims.
- [ ] Do not add biological rescue claims.
- [ ] Do not add dopamine equivalence or disease-severity mapping.
- [ ] Do not add mechanistic equivalence claims.
- [ ] Do not add statistical-significance claims.

## Repository Checks

- [ ] Confirm `main` is the canonical release branch.
- [ ] Confirm Release `v1.0.0` is the cited release.
- [ ] Confirm GitHub Actions pass on the submission commit.
- [ ] Confirm all referenced figures, tables, evidence files, and release
      artifacts exist.
- [ ] Confirm no frozen implementation, evidence, notebook, manuscript, or
      release artifact was modified.
