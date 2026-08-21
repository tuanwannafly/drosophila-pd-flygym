# Repository Architecture

This is the architecture snapshot for the Research Repository Migration (V3
Preparation). It describes the repository at commit `125cdff` and is an
orientation document, not a promise of future functionality.

## Purpose and boundaries

The repository is research software for computational Drosophila locomotion.
The scientific chain is frozen through Milestone F. V2 modules are additive
software for imported rollouts, analysis, workflow management, and presentation.
No repository layer should present simulation output as direct evidence from
real flies or as validation of a Parkinson's disease model.

## Directory tree

```text
src/drosophila_pd/       importable Python package
configs/                 experiment, analysis, and V2 configuration
scripts/                 explicit command-line entry points
tests/                   Python regression and contract tests
web/                     Fly Studio browser application
notebooks/               historical/session research interfaces
results/                 selected small evidence and generated artifacts
dist/                    frozen final report deliverables
docs/                    scientific, release, V2, and developer documentation
research/                reserved research workspace anchors
templates/               reusable research-document templates
reproducibility/         environment and reproduction policy records
```

The new `research/` and `templates/` directories are organizational. Their
README and template files do not contain rollout data or fabricated results.

## Module map

| Area | Location | Responsibility | Status |
| --- | --- | --- | --- |
| Anatomy | `src/drosophila_pd/anatomy/` | FlyGym anatomy audits and the authorized materialization gate | Stable/frozen checkpoints |
| Controllers | `src/drosophila_pd/controllers/` | Baseline controller configuration and construction | Stable scientific infrastructure |
| Experiments | `src/drosophila_pd/experiments/` | Baseline, perturbation, sweep, robustness, rescue, and refresh runners | Stable/frozen evidence pipeline |
| Metrics | `src/drosophila_pd/metrics/` | Locomotion, gait, turning, open-field, and trajectory measurements | Stable analysis layer |
| Perturbations | `src/drosophila_pd/perturbations/` | Explicit generic perturbation interfaces | Stable computational interface |
| Evidence analysis | `src/drosophila_pd/analysis/` | CPU-only synthesis of frozen evidence | Stable/frozen analysis |
| Scientific validation | `src/drosophila_pd/scientific_validation/` | Reference comparisons, reproducibility, statistics, reports, and figures | Stable validation layer |
| Behavioral platform | `src/drosophila_pd/behavior_platform/` | Rollout post-processing, assays, gait, open field, digital twin, campaign, AI, and export services | Additive V2 platform |
| Automation | `src/drosophila_pd/automation/` | Dataset catalog, artifact, publication, health, benchmark, and reproducibility orchestration | Additive V2 platform |
| Experiment management | `src/drosophila_pd/experiment/` and `src/drosophila_pd/research_campaign/` | Caller-provided experiment jobs and campaign lifecycle records | Additive orchestration |
| Fly Studio | `src/drosophila_pd/flystudio/` and `web/` | Imported-project exchange, playback, viewer, and browser workspace | Additive presentation layer |
| Digital twin | `src/drosophila_pd/digital_twin_platform/` | Twin records, snapshots, state diffs, annotations, and sessions | Additive workflow layer |

## Package map

The `src` layout is configured in `pyproject.toml` with automatic discovery for
`drosophila_pd*`. The import package contains 187 Python files at this
checkpoint, including the root package, 16 named top-level subpackage areas,
and the nested `flystudio.integration` subpackage. `__pycache__` directories
are local build outputs and are ignored by Git.

The package root exposes version metadata through
`importlib.metadata.version()` and provides the documented orchestration and
platform aliases listed in [the public API](public_api.md). Subpackages retain
their own explicit `__all__` declarations where a public surface is intended.

## Dependency map

```text
configs -> scripts -> experiments/controllers/perturbations -> results
rollout arrays -> behavior_platform/metrics/assays -> reports/figures/tables
existing artifacts -> automation/research_campaign/research_pipeline
frozen evidence -> analysis/evidence_synthesis -> E6 figures/tables -> report
imported project JSON -> flystudio Python modules -> web/ viewer modules
```

Runtime dependencies declared in `pyproject.toml` are NumPy, PyYAML, and
Matplotlib. Testing uses pytest. DOCX/PDF packaging uses the optional `docs`
dependencies. FlyGym and MuJoCo are optional simulation dependencies and are
not required for CPU-only evidence analysis or documentation work.

## Public APIs

The root package exports version information and selected automation, Digital
Twin, research-campaign, and unified-study symbols. The broad V2 surface is
documented in its package documentation and in [public_api.md](public_api.md).
The web application has JavaScript module exports documented by the existing
release-candidate API inventory; it is not a Python import surface.

## CLI inventory

| Command family | Entry point | Role |
| --- | --- | --- |
| Anatomy/evidence | `audit_block_8_12.py`, `audit_block_8_13.py`, `run_joint_materialization_milestone.py` | Frozen anatomy checkpoints |
| Simulation evidence | `run_healthy_baseline.py`, `run_perturbation_experiment.py`, `run_parameter_sweep.py`, `run_combined_phenotype_sweep.py`, `run_candidate_robustness.py`, `run_phenotype_concordance.py`, `run_computational_rescue.py` | Authorized FlyGym/MuJoCo or evidence-stage commands |
| Measurement | `run_g7_measurement_refresh.py` | Measurement-enabled rollout refresh |
| Analysis/build | `run_evidence_synthesis.py`, `build_final_report.py`, `validate_scientific_pipeline.py` | Evidence synthesis, report packaging, validation |
| Workflow | `run_experiment.py`, `run_study.py`, `research_campaign_cli.py`, `research_automation_cli.py`, `digital_twin_platform_cli.py` | Caller-provided orchestration and metadata |
| Project exchange | `build_demo_project.py`, `import_flystudio_project.py`, `export_flystudio_project.py` | Fly Studio project exchange and smoke fixtures |

CLI commands are explicit interfaces. A command that needs FlyGym must be run
in the documented compatible environment; metadata-only commands do not create
scientific rollouts.

## Documentation inventory

Documentation is organized into scientific evidence (`docs/scientific/`),
traceability and session history, report/submission/archive material, V2 module
guides under `docs/v2/`, Vietnamese guides under `docs/vi/`, release reports,
and the new hub pages under `docs/`. The canonical manuscript remains
`docs/report/final_report.md`.

## Generated and frozen artifacts

The selected evidence reports and E6 tables/figures under `results/` are
version-controlled using narrow `.gitignore` allowlists. The three final report
files under `dist/` are frozen and version-controlled. Large/raw rollout,
video, archive, and binary experiment outputs remain ignored unless explicitly
curated.

## Stability classification

| Classification | Meaning in this repository |
| --- | --- |
| Stable | Existing scientific pipeline, package installation, frozen evidence readers, and documented public workflow |
| Additive V2 | Implemented and tested platform services that operate on imported artifacts; they do not alter frozen V1 results |
| Experimental | New research-facing integrations, optional exporters, and interfaces whose long-term API is not yet promised |
| Internal | Private helpers, generated reports, implementation details, and `_`-prefixed symbols |
| Deprecated | No repository API is explicitly marked deprecated at this checkpoint |

## Frozen scientific boundary

Milestones C-F, frozen evidence JSON, the manuscript, report deliverables, and
historical notebooks are preserved. `PARTIAL_PHENOTYPE_CONCORDANCE` remains
qualitative. The repository does not claim Parkinson's disease validation,
biological rescue, dopamine equivalence, disease-severity mapping, mechanistic
equivalence, or statistical significance.

## Maintenance notes

The release-candidate health report records no local dependency cycles and no
missing required release modules. It also records informational duplicate
module names and unused-export/import findings. Those are documented technical
debt, not silently removed during this migration.
