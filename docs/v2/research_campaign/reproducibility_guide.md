# Reproducibility Guide

The campaign engine records:

- current git commit;
- campaign ID;
- normalized configuration hash;
- dataset hash;
- artifact hashes;
- Python version;
- seed list;
- timestamp;
- platform and executable path.

Use `replay_campaign_plan` to reconstruct the experiment plan from a config.
Use `verify_campaign_replay` to compare the reconstructed plan with a stored
manifest. Use `verify_artifact_hashes` and `verify_dataset_package` to check
artifact and dataset integrity.

The replay check validates campaign identity and artifact integrity. It does not
prove biological reproducibility or statistical significance.
