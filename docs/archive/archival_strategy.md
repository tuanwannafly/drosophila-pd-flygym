# Archival Strategy

The primary archival unit is repository version 1.0.0 on the canonical `main`
branch and Release `v1.0.0`. GitHub remains the source of truth for the live
repository state. External archives should preserve the release snapshot
without rewriting frozen evidence or report artifacts.

## Preferred Archival Targets

- GitHub Release `v1.0.0` for repository-native distribution.
- Zenodo for DOI minting, if enabled by the project owner.
- Software Heritage for source-code preservation.
- OSF, Figshare, or an institutional repository for supplementary artifact
  deposits if required by a venue.

No external DOI or archive deposit is declared in the repository unless it is
created by an actual archival event.

## Deposit Contents

An archive deposit should include:

- complete source tree
- `LICENSE`
- `CITATION.cff`
- `docs/citation.md`
- `docs/release/v1.0.0.md`
- `docs/report/`
- `dist/Drosophila_PD_FlyGym_Final_Report.pdf`
- `dist/Drosophila_PD_FlyGym_Final_Report.docx`
- `dist/final_report_manifest.json`
- frozen evidence JSON files under `results/`
- E6 figures and CSV tables
- `docs/publication/`
- `docs/submission/`
- `docs/archive/`

Large raw artifacts should remain outside Git unless explicitly curated for an
external archive deposit.

## Change Control

Frozen v1.0.0 artifacts should not be edited in place. Any future scientific,
software, or evidence update should use a new commit and, if public, a new
versioned release.
