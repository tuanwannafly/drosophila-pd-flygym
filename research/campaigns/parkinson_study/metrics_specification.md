# Metrics Specification

Project B reuses existing output keys and modules only.

## Locomotion and body

Use existing planar displacement, path length, trajectory efficiency, mean
planar speed, body-height summaries, yaw change, sample/step counts, finite
flags, and controller-action summaries from
`src/drosophila_pd/metrics/locomotion.py` and `trajectory.py`.

## Behavior and trajectory

When the rollout contains the required arrays, reuse walking/pause bouts,
walking duty cycle, yaw rate, turn bouts, cumulative turning, left/right
asymmetry, open-field metrics, heading, instantaneous speed, and cumulative
distance from the existing metrics and assay modules.

## Validation and reporting

Use existing finite-value, actuator, deterministic-seed, manifest, frame-count,
and checksum checks. Statistics and reports must preserve units, denominators,
missingness, and provenance.

No metric is designated as a biological PD endpoint. Unsupported observables
remain unsupported; Project B does not calculate replacements.
