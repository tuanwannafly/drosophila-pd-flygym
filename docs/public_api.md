# Public API Reference

This reference is intentionally concise. It lists the import surfaces that are
documented for reuse; it does not turn every implementation helper into a
stable API. The source code and each package's `__init__.py` remain authoritative.

## Package installation

```bash
python -m pip install -e .
python -c "import drosophila_pd; print(drosophila_pd.__version__)"
```

## Root Python package

`drosophila_pd` publicly exposes:

- `__version__`
- automation services such as `DatasetCatalog`, `ArtifactManager`,
  `ProjectHealthMonitor`, `PublicationBuilder`, and `ResearchAutomationPlatform`
- Digital Twin platform records and managers
- research campaign records and managers, exported with
  `ResearchCampaign...` compatibility aliases
- `StudyRequest`, `StudyDatasetInput`, `StudyOrchestrator`, `StudyResult`, and
  `run_study`

The root package does not import FlyGym. Simulation-specific imports occur in
the experiment modules that need them.

## Stable scientific and evidence APIs

| Package | Representative public symbols |
| --- | --- |
| `drosophila_pd.anatomy` | `build_block_8_12_report`, `build_block_8_13_orientation_report`, `materialize_joints_explicit_gate`, `build_milestone_8b_materialization_report` |
| `drosophila_pd.controllers` | `CPGControllerConfig`, `build_official_cpg_controller` |
| `drosophila_pd.experiments` | `run_healthy_baseline`, `run_paired_perturbation_experiment`, `run_parameter_sweep`, `run_combined_phenotype_sweep`, `run_candidate_robustness_validation`, `run_computational_rescue_validation` |
| `drosophila_pd.metrics` | Locomotion, trajectory, turning, open-field, and gait metric functions documented in the package modules |
| `drosophila_pd.analysis` | `run_evidence_synthesis`, `load_evidence_reports`, `validate_frozen_evidence`, `generate_tables`, `generate_figures` |
| `drosophila_pd.scientific_validation` | Reference datasets, comparison metrics, reproducibility checks, statistics, reports, and visualization helpers |

The anatomy materialization gate is intentionally explicit. Code outside the
authorized gate must not call `add_joints()`, assign `fly.skeleton`, or mutate
MJCF.

## Behavioral platform APIs

The additive V2 package exports data models (`RolloutData`, `BehaviorEpisode`,
`BehaviorSequence`, `Arena`, `ProgressionStage`, `DigitalTwin`, and related
records), post-processing functions (`analyze_gait`, `analyze_open_field`,
`measure_rollout_behavior`, `compare_rollouts`), assay classes, campaign and
dataset helpers, visualization/export functions, intervention/progression
records, and AI dataset/feature/report helpers.

Package-level exports are listed in
`src/drosophila_pd/behavior_platform/__init__.py`. Module-level details are in
`docs/v2/behavior_platform/`, `docs/v2/gait_platform/`,
`docs/v2/open_field/`, `docs/v2/digital_twin/`, and
`docs/v2/ai_platform/`.

## Orchestration APIs

The following are management layers over caller-provided artifacts:

- `drosophila_pd.experiment`: `ExperimentJob`, `ExperimentRunner`,
  `ExperimentQueue`, `ExperimentScheduler`, `ExperimentManifest`, and
  `ExperimentResult`.
- `drosophila_pd.research_campaign`: `Campaign`, `CampaignManager`,
  `CampaignManifest`, `CampaignState`, `CampaignHistory`, and event records.
- `drosophila_pd.research_pipeline`: `StudyOrchestrator`, `StudyRequest`, and
  `run_study`.
- `drosophila_pd.automation`: dataset catalogs, artifact management,
  publication builders, health, benchmarks, developer inspection, and
  reproducibility services.

These APIs do not fabricate rollout data. A real simulation or imported dataset
must be supplied by the caller and any FlyGym run must use the documented
environment.

## CLI entry points

The supported executable interfaces are listed in
[repository_architecture.md](repository_architecture.md#cli-inventory). Run
`python scripts/<name>.py --help` for command-specific options. Scripts are
thin orchestration boundaries; reusable behavior belongs in `src/`.

## Web API surface

The browser application under `web/` uses ES modules rather than a package
installer. Its release-candidate inventory in
`docs/release_candidate/api_index.json` records JavaScript module exports for
the loader, workspace, viewer, playback, analysis, statistics, plugin, and
export layers.

## Compatibility policy

The frozen V1 scientific API and evidence formats have priority. V2 interfaces
are additive and should preserve existing imports where practical. Changes to
public symbols should include tests, documentation, and a migration note.
