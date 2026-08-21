# Reproducibility

## Repository and environment

GitHub is the repository source of truth. The canonical reusable logic lives
under `src/drosophila_pd`; scripts are thin execution interfaces; notebooks are
historical research interfaces. The frozen simulation evidence was produced in
Google Colab with:

- Python 3.12.13
- FlyGym 2.1.0
- MuJoCo 3.9.0

The analysis synthesis uses the repository's Python analysis dependencies and
does not require a new FlyGym/MuJoCo simulation.

## Frozen evidence commands

The following commands identify the canonical entry points. Upstream commands
are shown for reproducibility and require their recorded Colab environment;
they are not required to read this report.

| Stage | Command or artifact |
| --- | --- |
| Block 8.12 | `python scripts/audit_block_8_12.py --output results/baseline/block_8_12_audit.json` |
| Block 8.13 | `python scripts/audit_block_8_13.py --output results/baseline/block_8_13_orientation.json` |
| Milestone 8B | `python scripts/run_joint_materialization_milestone.py --output results/baseline/milestone_8b_materialization.json` |
| Milestone C | `python scripts/run_healthy_baseline.py --output results/baseline/healthy_baseline.json` |
| Milestone D identity/action | `python scripts/run_perturbation_experiment.py --baseline-config configs/experiments/healthy_baseline.yaml --perturbation-config configs/experiments/perturbations/<identity-or-action>.yaml --output results/perturbations/<experiment>.json` |
| Milestone E1 | `python scripts/run_parameter_sweep.py --baseline-config configs/experiments/healthy_baseline.yaml --sweep-config configs/experiments/sweeps/milestone_e1.yaml --output results/sweeps/milestone_e1.json` |
| Milestone E2 | `python scripts/run_combined_phenotype_sweep.py --baseline-config configs/experiments/healthy_baseline.yaml --sweep-config configs/experiments/sweeps/milestone_e2.yaml --output results/sweeps/milestone_e2_combined.json` |
| Milestone E3 | `python scripts/run_candidate_robustness.py --baseline-config configs/experiments/healthy_baseline.yaml --validation-config configs/experiments/validation/milestone_e3.yaml --output results/validation/milestone_e3_candidate_robustness.json` |
| Milestone E4 | `python scripts/run_phenotype_concordance.py --matrix docs/scientific/e4_evidence_matrix.yaml --e3-evidence results/validation/milestone_e3_candidate_robustness.json --output results/validation/milestone_e4_concordance.json` |
| Milestone E5 | `python scripts/run_computational_rescue.py --baseline-config configs/experiments/healthy_baseline.yaml --validation-config configs/experiments/validation/milestone_e5.yaml --output results/validation/milestone_e5_computational_rescue.json` |
| Milestone E6 | `python scripts/run_evidence_synthesis.py --config configs/analysis/milestone_e6.yaml --output results/analysis/milestone_e6_synthesis.json` |

The exact script options and configuration files in the repository are
authoritative if a historical command has changed. Frozen report paths, not
notebook cell order, define the evidence inputs.

## Evidence provenance

The E6 synthesis records `synthesis_git_commit` as
`53e41d17365f56509ca708ba3352ddf724b0e89a` and represents exactly eight input
reports. The input commits recorded by the manifest are:

| Evidence | Commit |
| --- | --- |
| Unperturbed baseline | `91bc44c25dd25ea1ac409001efafc74dda018ce8` |
| Milestone D identity | `f886c204d8ad3a95dcd953418a8f9df51927137f` |
| Milestone D action scale | `f886c204d8ad3a95dcd953418a8f9df51927137f` |
| Milestone E1 | `7cb2ed580b8eabb6a363b27f481564751eeb9e48` |
| Milestone E2 | `433269ed11e0475eb973b62d31f469d66843872f` |
| Milestone E3 | `730ab3acd8e5535b93f320a62c19080feca0448f` |
| Milestone E4 | `9a13b43b2619e2423c96cf390a3dcbddc9f248fe` |
| Milestone E5 | `7cffac001488589d089bc49266aa103e7458f476` |

The E6 report includes SHA-256 values for all eight inputs and reports 56
passed checks. It also records `synthesis_worktree_dirty = true`. At synthesis
time, that flag was attributable solely to the known out-of-scope historical
Session 02 notebook, which was deliberately preserved. Later documentation
changes do not rewrite that historical provenance field.

## Verification commands

From the repository root:

```bash
python -m compileall -q src scripts tests
pytest -q -rs -p no:cacheprovider
git diff --check
```

To inspect the frozen artifact inventory:

```bash
Get-ChildItem results/analysis/figures
Get-ChildItem results/analysis/tables
```

The expected E6 inventory is four PNG figures and five CSV tables, in addition
to the synthesis JSON. The E6 run validates these paths and their content
schema. The JSON and generated artifacts are version-controlled through narrow
allowlists; unrelated generated results remain ignored.

## Historical notebooks

The Session 01 and Session 02 notebooks document historical execution and
orientation work. They are not required to execute E6. The dirty Session 02
notebook is intentionally not modified, staged, or normalized as part of this
report package.
