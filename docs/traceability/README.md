# Phase G2 Traceability and Provenance Graph

This directory records the canonical relationship between historical research
notebooks, reusable repository code, frozen milestones, evidence JSON,
analysis artifacts, manuscript sections, and the v1.0.0 release.

## Scope

Phase G2 is read-only analysis. It does not alter frozen implementations,
evidence JSON, manuscript files, report artifacts, release files, or the
protected Session 02 notebook. It does not run notebooks, FlyGym, MuJoCo, or
any simulation.

The completed Phase G1 inventory is the notebook source for this graph:

- `docs/session_inventory/session_index.md`
- `docs/session_inventory/session01_traceability.yaml`
- `docs/session_inventory/session02_traceability.yaml`
- `docs/session_inventory/canonical_mapping.csv`

## Files

- `artifact_graph.yaml`: canonical node, edge, and per-milestone contract
  representation.
- `artifact_graph.csv`: flat CSV projection of the principal nodes and edges.
- `milestone_dependency_matrix.csv`: ordered milestone dependencies from 8B
  through the final release.
- `provenance_chain.md`: narrative historical-notebook-to-release chain.
- `claim_traceability.csv`: report claim to evidence, figure/table, paper
  section, and validation class.
- `validation_traceability.csv`: validation coverage by milestone and type.

## Edge policy

An edge is included only when it is supported by one or more of:

- the Phase G1 mapping;
- an explicit import, configuration path, or CLI command in the repository;
- an evidence JSON path or provenance field;
- an E6 artifact manifest;
- a report claim/evidence table, manuscript reference, or release note; or
- repository history and the frozen release manifest.

`none` in a table means that no direct artifact was found. It is not a claim
that an unlisted relationship does not exist scientifically.

## Frozen provenance anchors

- Release tag: `v1.0.0`
- Release commit: `b06bef93b9a12d921377ad72ee85d1ad2a4f44a0`
- Canonical manuscript source commit:
  `004488cf7fd5e980137a209d360b977716865e1a`
- Milestone F build implementation commit:
  `82746cf1276d3edf7e8ce3206d83f49b3470e1dd`
- Final artifact freeze commit:
  `d0287fb0ed5a9a2849762cc5f6a1bb9aa107f030`
- E6 synthesis implementation commit:
  `53e41d17365f56509ca708ba3352ddf724b0e89a`

The evidence reports retain their own execution commit fields. The graph does
not rewrite those fields or treat later documentation commits as evidence
execution commits.

## Known limitations

- Historical notebook cells are not individually linked to execution IDs or
  hashes inside the evidence JSON reports.
- Session 01 has no direct evidence JSON; its setup ideas are mapped to the
  canonical implementations only where the repository history supports that
  relationship.
- E6 consumes eight upstream reports and therefore does not subsume the
  separate 8.12, 8.13, or 8B evidence files.
- The E6 JSON retains the historical internal status value
  `E6=IMPLEMENTED_AWAITING_REVIEW`; the subsequent E6 freeze documentation
  and v1.0.0 release record E6 as frozen. Both facts are preserved here.
- A `none` figure/table entry in claim traceability is an explicit absence of
  a dedicated visual/table artifact, not an invented mapping.

## Scientific boundary

The graph describes a computational/phenomenological simulation framework and
its evidence packaging. `PARTIAL_PHENOTYPE_CONCORDANCE` remains qualitative.
The graph introduces no claim of Parkinson's disease validation, biological
rescue, dopamine equivalence, disease severity mapping, mechanistic
equivalence, or statistical significance.
