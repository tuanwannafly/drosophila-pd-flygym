# 137. Table Specification

These tables are planning targets only. No result table is generated until
real, approved rollout data has passed the dataset contract.

| Table | Content | Source | Required controls |
| --- | --- | --- | --- |
| 1 | Dataset summary | Manifest, metadata, checksum | Version, entries, missing files, byte sizes |
| 2 | Experiment summary | Experiment matrix and completed manifests | ID, seed, status, configuration, outputs |
| 3 | Motor features | Locomotion and controller-action summaries | Units, finite values, action/adhesion availability |
| 4 | Statistics | Existing report/statistical outputs | Denominators, missingness, seed handling, method provenance |
| 5 | Validation | Validation and integrity reports | Check name, expected, observed, pass, limitations |
| 6 | Reproducibility | Commit, environment, configuration, checksums | Full provenance and artifact hashes |

Tables must distinguish missing, unavailable, and not measured. None of these
tables is a biological validation table.
