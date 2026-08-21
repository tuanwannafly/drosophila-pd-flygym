# Research Campaign API

Public API is exported from `drosophila_pd.behavior_platform`.

Planning:

- `CampaignConfig`
- `ExperimentPlan`
- `create_campaign`
- `generate_experiment_matrix`
- `CampaignScheduler`
- `load_campaign_config`
- `save_campaign`

Execution orchestration:

- `CampaignRunner`
- `CampaignCheckpoint`
- `CampaignResume`
- `CampaignHistory`
- `resume_campaign`

Data and artifacts:

- `CampaignDatasetBuilder`
- `merge_campaign_datasets`
- `validate_campaign_dataset`
- `load_campaign_results`
- `CampaignArtifactManager`
- `deterministic_artifact_layout`
- `artifact_manifest_from_paths`

Figures and paper assets:

- `CampaignFigureFactory`
- `generate_paper_assets`

Provenance and reproducibility:

- `CampaignProvenance`
- `collect_campaign_provenance`
- `write_provenance_manifest`
- `file_sha256`
- `stable_hash`
- `directory_manifest`
- `replay_campaign_plan`
- `verify_campaign_replay`
- `verify_artifact_hashes`
- `verify_dataset_package`
- `verify_manifest_signature`

All functions are deterministic for fixed inputs, except timestamps and current
git metadata recorded in provenance manifests.
