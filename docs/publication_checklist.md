# Publication Checklist

This checklist prepares repository version 1.0.0 for public scientific
dissemination. It is a release-readiness document only. It does not change
scientific implementation, simulations, frozen evidence, manuscript contents,
release artifacts, notebooks, or experimental results.

## GitHub Release Checklist

- [ ] Confirm `main` is the canonical release branch.
- [ ] Confirm Release v1.0.0 points to the intended release commit.
- [ ] Attach or reference the final report artifacts:
  - `dist/Drosophila_PD_FlyGym_Final_Report.docx`
  - `dist/Drosophila_PD_FlyGym_Final_Report.pdf`
  - `dist/final_report_manifest.json`
- [ ] Include `docs/release/v1.0.0.md` as release-note source.
- [ ] Verify README badges, release link, citation link, report links, and
      community links.
- [ ] Confirm GitHub Actions pass on `main`.
- [ ] Confirm no frozen evidence, manuscript, notebooks, or release artifacts
      changed after the release freeze.

## Zenodo Checklist

- [ ] Enable or confirm GitHub-Zenodo integration for the repository.
- [ ] Archive Release v1.0.0.
- [ ] Confirm archived files include the final report, evidence JSON, figures,
      tables, license, citation metadata, and release notes.
- [ ] Confirm Zenodo metadata does not claim a journal article, biological
      validation, Parkinson's disease validation, dopamine equivalence,
      disease-severity mapping, biological rescue, mechanistic equivalence, or
      statistical significance.
- [ ] Record the Zenodo DOI after it is minted.
- [ ] Add DOI metadata only after the DOI exists.

## DOI Checklist

- [ ] Do not invent a DOI before archival.
- [ ] After Zenodo archival, verify the DOI resolves.
- [ ] Verify the DOI points to Release v1.0.0 or the intended archived version.
- [ ] Update citation instructions only after the DOI is real and resolvable.
- [ ] Preserve `CITATION.cff` provenance fields and version identity.

## Preprint Checklist

- [ ] Confirm the final manuscript source remains frozen.
- [ ] Use the final PDF artifact as the preprint submission file if accepted by
      the selected server.
- [ ] Include the repository URL and Release v1.0.0.
- [ ] Include the final report manifest or artifact hash information where
      appropriate.
- [ ] Preserve the scientific boundary: computational/phenomenological model
      only, qualitative concordance only, no biological validation claim.
- [ ] Do not introduce new claims, data, simulations, or parameter tuning in the
      preprint metadata.

## Journal Submission Checklist

- [ ] Confirm author, affiliation, and journal-specific metadata outside this
      repository before submission.
- [ ] Use `docs/report/final_report.md` and the generated PDF/DOCX artifacts as
      the source package.
- [ ] Include figures from `results/analysis/figures/`.
- [ ] Include tables from `results/analysis/tables/`.
- [ ] Include reproducibility and provenance statements from the final report.
- [ ] Ensure all claims remain within the computational evidence boundary.
- [ ] Treat any requested scientific changes as a new authorized revision, not
      as an edit to the frozen v1.0.0 release.

## Artifact Checklist

- [ ] Final report DOCX present.
- [ ] Final report PDF present.
- [ ] Final report manifest present.
- [ ] Frozen baseline, perturbation, sweep, validation, and synthesis JSON files
      present.
- [ ] E6 figures present.
- [ ] E6 tables present.
- [ ] Release notes present.
- [ ] `LICENSE` present.
- [ ] `CITATION.cff` present.
- [ ] `docs/citation.md` present.

## Long-Term Archival Checklist

- [ ] Archive the GitHub release.
- [ ] Archive final report artifacts.
- [ ] Archive frozen evidence JSON.
- [ ] Archive E6 figures and tables.
- [ ] Archive citation and license files.
- [ ] Preserve Git commit, release tag, and artifact hashes.
- [ ] Record external DOI only after minting.
- [ ] Keep large raw artifacts outside Git unless explicitly curated for an
      archive deposit.
- [ ] Preserve notebooks as historical research records without executing or
      rewriting them.
