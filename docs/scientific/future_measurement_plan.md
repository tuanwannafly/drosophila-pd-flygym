# G4 Future Measurement Plan

This plan identifies measurements that would improve biological endpoint
coverage after Release v1.0.0. It is not an implementation authorization and it
does not change frozen milestone conclusions.

## Highest-Value Additions

### P1. Bout and Pause Segmentation

Add flat-ground movement-bout labels from time-resolved position or speed:
moving fraction, pause count, pause duration, stop duration, distance per
movement, and per-bout speed.

Supported gaps:

- Chen 2014 distance per movement.
- Kajtor 2025 stop durations.
- General freezing or pause behavior.

Required controls:

- Prespecified speed threshold or state classifier.
- Sensitivity analysis for threshold choice.
- Separate reporting from existing path length and displacement.

### P1. Time-Resolved Turning

Add yaw-rate, angular speed, turn-event count, turn duration, and turn-direction
asymmetry from orientation time series.

Supported gaps:

- Chen 2014 angular velocity.
- Trial-based turning behavior if a stimulus assay is later introduced.

Required controls:

- Do not reuse run-level yaw change as angular velocity.
- Preserve existing yaw change as a computational descriptor.

### P1. Open-Field and Stimulus-Response Assays

Add explicit assay geometry and trial structure before mapping open-field or
threat-response endpoints:

- center/periphery occupancy for centrophobism,
- wall proximity,
- stimulus onset times,
- stimulus-aligned speed and heading,
- trial reactivity fraction.

Supported gaps:

- Chen 2014 centrophobism.
- Kajtor 2025 reactivity and threat-assay speed context.

## Medium-Priority Additions

### P2. Vertical Climbing / SING

Design a separate vertical assay rather than retrofitting flat-ground outputs.
Candidate observables include climb success fraction, vertical displacement,
climb velocity, time-to-threshold, and fall or stall events.

Supported gaps:

- Riemensperger 2011 negative geotaxis.
- Riemensperger 2013 climbing deficits.
- Aggarwal 2019 automated climbing.
- Liu 2008 climbing.
- Coulom 2004 negative geotaxis.

### P2. Gait and Inter-Leg Coordination

First perform a targeted adult Parkinson gait-literature pass, because G3 found
no directly curated adult PD inter-leg coordination paper mapped to current
evidence. Candidate observables include stance/swing state, inter-leg phase,
tripod regularity, duty factor, contact timing, and coordination variability.

Adhesion duty and transition counts are useful software descriptors, but they
are not sufficient as biological gait coordination metrics.

## Lower-Priority or Separate Assay Families

### P3. Tremor Metrics

Tremor should be added only after choosing a validated signal source and
frequency band. Candidate sources could include limb trajectories, joint angles,
body pose, or PER-specific signals if a PER assay exists.

### P3. Proboscis Extension Response

PER speed and duration variability are separate motor-reflex endpoints. They
should not be mapped to whole-body walking speed.

### P3. Biological Treatment or Rescue Mapping

Biological rescue endpoints from L-DOPA, Mucuna, toxin, or drug studies require
a new bridge between experimental treatment and simulation intervention.
Milestone E5 remains computational reversibility only and must not be treated
as a biological rescue assay.

## Recommended G5

G5 should choose one measurement family for a prespecified implementation plan.
The best candidates are bout/pause segmentation plus yaw-rate turning, because
they can extend the existing flat-ground output pipeline without requiring a new
world geometry. Open-field center avoidance and vertical climbing should be
designed as separate assays.
