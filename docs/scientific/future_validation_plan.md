# G6 Future Validation Plan

This plan records what evidence would be needed to validate additional
computational phenotypes after G6. It is not authorization to rerun simulations
or modify frozen milestones.

## Preserve Existing Supported Endpoints

The current supported endpoint is adult walking speed / velocity / mean speed.
Future runs should continue reporting `mean_planar_speed_mm_s` and should add
the G5 instantaneous-speed time series when raw arrays are available.

Distance-like output should continue using `planar_path_length_mm` as primary
and `planar_displacement_mm` as supplemental. Direct experimental calibration
should remain prohibited unless a later authorized validation design supplies
the required bridge.

## First G5 Validation Pass

The most useful next validation run would reuse the exact frozen candidate and
baseline parameters, but export raw thorax positions and quaternions for G5
analysis. The goal would be to compute:

- distance per movement,
- walking and pause bout counts,
- walking and pause durations,
- walking duty cycle,
- yaw rate,
- turn bouts,
- cumulative turning,
- left/right asymmetry,
- trajectory CSVs.

This would still be computational phenotype validation only. It should use the
same paired-seed design as E3 and should not tune the candidate.

## Open-Field Extension

Open-field endpoints require an explicitly declared virtual arena. Center
occupancy, border occupancy, radial distance, and exploration index should not
be computed as biological centrophobism unless the assay geometry and endpoint
definition are prespecified.

## Separate Assays

The following endpoints require new assay designs rather than analysis-only
extensions of the current flat-ground evidence:

- negative geotaxis / SING,
- climbing behavior,
- stimulus reactivity,
- proboscis extension response,
- tremor,
- biological treatment or rescue.

## Gait And Coordination

Adhesion duty and transition counts are not enough for inter-leg coordination.
A future gait milestone should first expand the adult Parkinson gait literature
inventory, then define phase, contact, stance/swing, and tripod regularity
metrics with prespecified validation rules.

## Recommended Next Phase

G7 should be a no-tuning raw-array export and analysis validation pass for the
existing frozen baseline/candidate pair. It should run the same candidate
parameters, same seed pairing, same controller, same world, and same duration
as E3, then compute G5 metrics from stored trajectories. Any disease language
must remain excluded unless external evidence and project-owner authorization
explicitly change the scientific stage.
