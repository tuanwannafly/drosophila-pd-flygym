# Dataset Adapter

`drosophila_pd.dataset_adapter` is the read-only intake boundary for FlyGym
outputs. `FlyGymDataset` contains manifest metadata, metadata-file references,
declared rollout files, observed hashes, and frame-count observations.

The adapter does not import FlyGym, MuJoCo, controllers, or simulation code.
It does not copy, rewrite, normalize, or delete a dataset.
