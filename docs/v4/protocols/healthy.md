# Healthy Experiment Protocol

## Objective

Run or analyze an unperturbed computational baseline using the frozen Healthy
configuration and authorized pipeline.

## Before execution

1. Record repository commit and configuration hash.
2. Verify Python 3.12, FlyGym 2.1.0, and MuJoCo 3.9.0 when simulation is needed.
3. Freeze seed, duration, timestep, controller, world, and output path.
4. Confirm the target evidence path is new and cannot overwrite frozen evidence.

## Outputs

Record rollout/measurement files, finite-value checks, metrics, logs, manifest,
and SHA-256 checksums. Classify results as computational baseline outputs only.

## Stop conditions

Stop for missing dependencies, changed configuration, non-finite observations,
missing provenance, or any request to interpret the output biologically.
