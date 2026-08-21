# Provenance Chain

## Chain overview

The repository-supported provenance chain is:

```text
historical notebook
    -> canonical implementation
    -> frozen evidence JSON
    -> manuscript and report artifacts
    -> v1.0.0 release
```

This chain records software and computational provenance. It does not promote
simulation output to biological validation.

## 1. Historical notebooks

Phase G1 reviewed exactly two notebooks:

- Session 01: `notebooks/session_01_environment/FlyBrain_Session01_Setup.ipynb`
  was created in `10e475d5e4190ce39dece9ed9b5f49637894b746` and organized with
  Session 02 in `1de7c8bfea84699fee2849d977a393013428739a`.
- Session 02:
  `notebooks/session_02_healthy_baseline/Session_02_Healthy_Baseline.ipynb`
  was created in `b5d3e85bfcb16e95ddda72998c17839389b741cb` and organized in
  `1de7c8bfea84699fee2849d977a393013428739a`.

The Session 02 notebook remains protected and dirty by prior work. It was not
modified or executed during G2. The G1 YAML and CSV inventory is the supported
mapping from notebook blocks to canonical code.

## 2. Canonical implementation

The historical anatomy sequence is represented by:

- Block 8.12: `src/drosophila_pd/anatomy/audit.py` and
  `scripts/audit_block_8_12.py`.
- Block 8.13: `src/drosophila_pd/anatomy/orientation.py` and
  `scripts/audit_block_8_13.py`.
- Milestone 8B: `src/drosophila_pd/anatomy/materialization.py` and
  `scripts/run_joint_materialization_milestone.py`.

The healthy simulation and controlled analysis chain is represented by the
baseline, perturbation, sweep, concordance, rescue, metrics, and synthesis
modules under `src/drosophila_pd`, with thin CLI entry points under `scripts/`.
The exact config-to-script commands are preserved in
`docs/report/reproducibility.md`.

Relevant implementation commits are recorded in the evidence JSON fields and
repository history, including:

| Stage | Implementation commit |
| --- | --- |
| Block 8.12 | `cabb8d5` |
| Block 8.13 | `6d22ac5` |
| Milestone 8B | `a43823a` |
| Milestone C | `91bc44c` |
| Milestone D | `f886c20` |
| Milestone E1 | `7cb2ed5` |
| Milestone E2 | `433269e` |
| Milestone E3 | `730ab3a` |
| Milestone E4 | `9a13b43` |
| Milestone E5 | `7cffac0` |
| Milestone E6 | `53e41d1` |

These short identifiers are navigation anchors; the full execution commits
remain in the JSON reports and `docs/report/reproducibility.md`.

## 3. Evidence JSON

The canonical runners write the following frozen reports:

1. `results/baseline/block_8_12_audit.json`
2. `results/baseline/block_8_13_orientation.json`
3. `results/baseline/milestone_8b_materialization.json`
4. `results/baseline/healthy_baseline.json`
5. `results/perturbations/identity.json`
6. `results/perturbations/action_scale_080.json`
7. `results/sweeps/milestone_e1.json`
8. `results/sweeps/milestone_e2_combined.json`
9. `results/validation/milestone_e3_candidate_robustness.json`
10. `results/validation/milestone_e4_concordance.json`
11. `results/validation/milestone_e5_computational_rescue.json`
12. `results/analysis/milestone_e6_synthesis.json`

E6 consumes exactly eight upstream reports: C, the two D reports, and E1-E5.
It generates four figures and five CSV tables. The E6 input commits and
SHA-256 values are authoritative in the frozen E6 JSON and
`results/analysis/tables/evidence_manifest.csv`.

The evidence reports are computational records. Their scope fields explicitly
exclude biological Parkinson's disease validation, mechanistic equivalence,
dopamine equivalence, disease severity mapping, biological rescue, and
statistical significance.

## 4. Paper and report artifacts

The canonical manuscript is `docs/report/final_report.md` at source commit
`004488cf7fd5e980137a209d360b977716865e1a`. Its claim-level source is
`docs/report/evidence_traceability.md`; its reproducibility commands and input
commits are in `docs/report/reproducibility.md`.

The manuscript maps the evidence chain into Methods Sections 2.1-2.11,
Results Sections 3.1-3.8, the Discussion and Limitations Sections 4-5,
Reproducibility Section 6, Conclusion Section 7, and Appendices A-C. The four
E6 figures are embedded in Results Sections 3.3-3.5 and 3.7. Manuscript Tables
2-4 summarize E3-E5; Table 1 records canonical conditions and parameters.

The claim and validation CSVs in this directory preserve explicit absences:
where the report has a text-only claim and no dedicated visual/table artifact,
the figure/table value is `none` rather than an invented link.

## 5. Release artifacts

Milestone F uses `scripts/build_final_report.py` to build the canonical source
into:

- `dist/Drosophila_PD_FlyGym_Final_Report.docx`
- `dist/Drosophila_PD_FlyGym_Final_Report.pdf`
- `dist/final_report_manifest.json`

The manifest preserves the manuscript source commit, build implementation
commit `82746cf1276d3edf7e8ce3206d83f49b3470e1dd`, artifact hashes, page count,
and validation results. The final artifact freeze commit is
`d0287fb0ed5a9a2849762cc5f6a1bb9aa107f030`.

Release `v1.0.0` is commit
`b06bef93b9a12d921377ad72ee85d1ad2a4f44a0`. Its release note explicitly lists
the frozen evidence chain and final artifacts. It also preserves the exact
scientific boundary: this is a computational/phenomenological framework;
`PARTIAL_PHENOTYPE_CONCORDANCE` is qualitative and no Parkinson's disease
validation claim is made.

## 6. Gaps and status discrepancies

- There is no cell-level execution hash linking either notebook output to a
  particular evidence JSON field.
- Session 01 has no direct report of its own; its reusable setup is supported
  through G1 mappings and later canonical runners.
- E6's JSON contains the historical internal value
  `milestone_status.E6=IMPLEMENTED_AWAITING_REVIEW`, while the later E6 freeze
  documentation and v1.0.0 release classify E6 as frozen. This graph preserves
  both values and does not rewrite the JSON.
- The known dirty Session 02 notebook is a worktree condition, not a scientific
  result or provenance replacement.
