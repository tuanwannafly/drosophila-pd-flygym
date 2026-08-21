# G3 Validation Gap Analysis

G3 expands the biological evidence context while preserving the Release v1.0.0
scientific boundary. The current repository remains a computational,
phenomenological framework. No G3 entry designates a Parkinson's disease
condition, dopamine-depletion value, disease stage, biological rescue, or
statistical-significance claim.

## Currently Covered

The strongest current correspondence is adult flat-ground locomotor output:

- Walking speed or velocity maps qualitatively to `mean_planar_speed_mm_s`.
- Covered or total moving distance maps partially to `planar_path_length_mm`,
  with `planar_displacement_mm` only as a supplemental endpoint.

These are direction-only mappings. They are useful for E4-style qualitative
concordance but cannot calibrate simulation parameters to experimental values.

## Partially Covered

Actometer or broad adult locomotor-activity endpoints can be considered only
partially covered. The repository records simulated path length, displacement,
speed, yaw displacement, body height, actions, and adhesion summaries, but it
does not reproduce actometer hardware, spontaneous activity sampling, or
long-duration circadian activity assays.

Threat-assay walking speed is also partial: `mean_planar_speed_mm_s` exists,
but there is no passing-shadow stimulus, trial alignment, or behavioral
response classification.

## Not Supported

The following adult Drosophila Parkinson locomotion endpoints are not supported
by current frozen evidence:

- negative geotaxis / SING performance
- vertical climbing success or climbing velocity
- movement-bout segmentation and distance per movement
- angular velocity and time-resolved turn rate
- open-field centrophobism or center occupancy
- freezing, stopping, pause duration, and trial reactivity
- PER speed, PER duration variability, and tremor
- inter-leg coordination phase or gait regularity
- biological L-DOPA, rotenone, Mucuna, or drug-rescue endpoints

## Candidate Future Measurements

Future work can improve literature comparability without changing frozen
Release v1.0.0 evidence:

1. Add bout segmentation for flat-ground walking: moving/stopped labels,
   distance per movement, pause count, pause duration, and duty of movement.
2. Add time-resolved turning metrics: yaw rate, angular speed, turn bouts, and
   turn-direction asymmetry.
3. Add an open-field assay geometry with center/periphery occupancy.
4. Add a vertical climbing or SING simulation design, keeping it separate from
   the current flat-ground baseline.
5. Add limb/gait observables only after defining a reliable joint or contact
   signal: inter-leg phase, stance/swing duration, tripod regularity, and
   coordination variability.
6. Add tremor-like metrics only from sufficiently high-rate position, joint, or
   appendage trajectories, with prespecified frequency bands.
7. Treat pharmacological and genetic-rescue literature as biological evidence
   only; do not map it onto computational reversibility without a new,
   prespecified bridge.

## Evidence Gaps

- Current E4 literature coverage used only two adult walking papers; G3 expands
  coverage but does not rerun E4.
- Most adult PD fly locomotion literature uses climbing, negative geotaxis, or
  assay-specific tracking endpoints that the repository does not yet measure.
- The current model has no direct biological genotype, toxin, dopamine, or drug
  perturbation implementation.
- The current body-height phenotype remains a simulation confound with no
  curated adult PD endpoint support.
- A previously referenced Block 8.13 orientation evidence JSON is absent from
  the current checkout; this is a traceability gap outside G3 literature
  mapping and was not reconstructed.

## Recommended G4 Mapping

G4 should convert this literature database into a formal endpoint-mapping
specification:

- preserve `SUPPORTED`, `PARTIALLY_SUPPORTED`, and `NOT_SUPPORTED` labels;
- define one row per literature endpoint and repository observable;
- add required assay metadata before any new comparison;
- prohibit calibration or disease-label assignment unless external evidence and
  explicit authorization are added;
- update E4 only after deciding whether the expanded literature scope should
  supersede or supplement the frozen Release v1.0.0 E4 matrix.
