# Artifact Manifest

This manifest summarizes the main archival artifacts for version 1.0.0. The
machine-readable final report artifact manifest is
`dist/final_report_manifest.json`.

## Final Report Artifacts

| Artifact | Path | Notes |
| --- | --- | --- |
| Final report DOCX | `dist/Drosophila_PD_FlyGym_Final_Report.docx` | Publication-format document artifact |
| Final report PDF | `dist/Drosophila_PD_FlyGym_Final_Report.pdf` | 14-page final report artifact |
| Final report manifest | `dist/final_report_manifest.json` | Byte sizes, SHA-256 hashes, provenance, validation |

## Frozen Evidence

| Artifact | Path |
| --- | --- |
| Block 8.12 audit | `results/baseline/block_8_12_audit.json` |
| Milestone 8B materialization | `results/baseline/milestone_8b_materialization.json` |
| Milestone C baseline | `results/baseline/healthy_baseline.json` |
| Milestone D identity | `results/perturbations/identity.json` |
| Milestone D action scale | `results/perturbations/action_scale_080.json` |
| Milestone E1 sweep | `results/sweeps/milestone_e1.json` |
| Milestone E2 combined sweep | `results/sweeps/milestone_e2_combined.json` |
| Milestone E3 robustness | `results/validation/milestone_e3_candidate_robustness.json` |
| Milestone E4 concordance | `results/validation/milestone_e4_concordance.json` |
| Milestone E5 reversibility | `results/validation/milestone_e5_computational_rescue.json` |
| Milestone E6 synthesis | `results/analysis/milestone_e6_synthesis.json` |

## Derived E6 Artifacts

| Artifact | Path |
| --- | --- |
| E1 response figure | `results/analysis/figures/e1_parameter_response.png` |
| E2 comparison figure | `results/analysis/figures/e2_condition_comparison.png` |
| E3 robustness figure | `results/analysis/figures/e3_paired_seed_robustness.png` |
| E5 reversibility figure | `results/analysis/figures/e5_computational_reversibility.png` |
| Evidence manifest table | `results/analysis/tables/evidence_manifest.csv` |
| E1 response table | `results/analysis/tables/e1_parameter_response.csv` |
| E2 summary table | `results/analysis/tables/e2_condition_summary.csv` |
| E3 seed table | `results/analysis/tables/e3_seed_summary.csv` |
| E5 reversibility table | `results/analysis/tables/e5_reversibility_summary.csv` |

## Citation And License

- `CITATION.cff`
- `docs/citation.md`
- `LICENSE`
- `docs/release/v1.0.0.md`
