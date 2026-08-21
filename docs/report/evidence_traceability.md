# Evidence Traceability

The table maps report-level claims to frozen artifacts. JSON field names refer
to the source report unless the path is an E6 generated table.

| ID | Report claim | Evidence path | Field or table | Boundary |
| --- | --- | --- | --- | --- |
| T01 | The unperturbed simulation baseline passed its software checks. | `results/baseline/healthy_baseline.json` | `overall_pass`, `environment`, `simulation`, `actuation`, `metrics` | Computational baseline only |
| T02 | Identity perturbation preserves the baseline. | `results/perturbations/identity.json` | identity comparison and zero-delta checks | Controlled software comparison |
| T03 | Global action scaling changes output and action magnitude as configured. | `results/perturbations/action_scale_080.json` | action-scale comparison and controlled-variable checks | Computational proxy |
| T04 | Motor-vigor response is graded across E1 scales. | `results/sweeps/milestone_e1.json` | motor family response records; `results/analysis/tables/e1_parameter_response.csv` | Computational response surface |
| T05 | Coordination has modest intermediate effects and a large near-zero effect. | `results/sweeps/milestone_e1.json` | coordination family response records; `e1_parameter_response.csv` | Computational response surface |
| T06 | Combined speed/displacement effects are mostly near additive and yaw is more nonlinear. | `results/sweeps/milestone_e2_combined.json` | interaction analysis; `results/analysis/tables/e2_condition_summary.csv` | Simulation interaction, not biology |
| T07 | The frozen candidate reduces displacement and speed across five paired seeds. | `results/validation/milestone_e3_candidate_robustness.json` | robustness assessment, aggregate, paired results; `e3_seed_summary.csv` | Computational robustness only |
| T08 | E4 has partial qualitative phenotype concordance. | `results/validation/milestone_e4_concordance.json` | concordance summary and endpoint classifications | Directional literature comparison only |
| T09 | E5 shows computational reversibility, especially on the motor axis. | `results/validation/milestone_e5_computational_rescue.json` | condition assessments and primary endpoint summary; `e5_reversibility_summary.csv` | Computational reversibility only |
| T10 | The frozen candidate is motor 0.8 and coupling 0.75. | `results/validation/milestone_e3_candidate_robustness.json`; `results/analysis/milestone_e6_synthesis.json` | candidate definition; `frozen_candidate_definition` | Candidate for further validation, not disease model |
| T11 | E6 passed 56 checks and synthesized eight inputs into four figures and five tables. | `results/analysis/milestone_e6_synthesis.json` | `overall_pass`, `checks`, `input_evidence_manifest`, `artifacts`, `provenance` | Evidence-only synthesis |
| T12 | No frozen result establishes biological PD validation or statistical significance. | `results/analysis/milestone_e6_synthesis.json` | `scientific_scope`, `scientific_synthesis`, `e4_concordance_summary`, `e5_reversibility_summary` | Explicit scientific boundary |

## Numerical consistency rule

The report uses the source units and precision where practical. Rounded values
in display tables are presentation values; the frozen JSON and CSV files remain
the authoritative numerical records. E1 path length and trajectory efficiency
are left absent because the E1 source report did not provide them. E5 control
and impaired reference rows have empty rescue-only fields by design. Neither
case is silently imputed.

## Provenance rule

E6's SHA-256 manifest and commit fields are evidence about the frozen synthesis
inputs. They are not regenerated or rewritten by this documentation package.
The known dirty historical Session 02 notebook is recorded as an excluded
worktree condition, not treated as a scientific result.
