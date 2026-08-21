# Random Seed Policy

Seed values are part of experiment provenance. A paired comparison must use the
same seed within each baseline/candidate pair and must record the complete seed
set. A sweep must record its configured values and condition order.

Changing a seed, duration, timestep, controller, environment, or perturbation
creates a new computational run and must not overwrite a frozen evidence file.
Seed reproducibility does not imply biological reproducibility.
