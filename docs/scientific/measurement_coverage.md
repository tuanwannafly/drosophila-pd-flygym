# G6 Measurement Coverage

G6 evaluates the frozen computational candidate against the endpoint map created
in G4 and the measurement capabilities added in G5. This is an evidence-only
assessment. It does not run FlyGym, MuJoCo, notebooks, or new analyses over raw
simulation data.

## Evidence Used

- E3 candidate robustness:
  `results/validation/milestone_e3_candidate_robustness.json`
- E4 qualitative concordance:
  `results/validation/milestone_e4_concordance.json`
- E5 computational reversibility:
  `results/validation/milestone_e5_computational_rescue.json`
- G3 adult Drosophila locomotion literature database:
  `docs/scientific/literature_database.yaml`
- G4 endpoint mapping:
  `docs/scientific/biological_mapping.yaml`
- G5 measurement modules under `src/drosophila_pd/metrics/`

## Supported By Frozen Candidate Evidence

Adult walking speed / velocity / mean speed is supported as a computational
phenotype. The frozen candidate has lower mean planar speed than the paired
baseline across all five E3 seeds, and E4 records qualitative direction-only
adult walking concordance.

## Partially Supported

Covered distance / total moving distance is partially supported. E3 records
lower displacement and lower path length in the candidate, while E4 treats path
length as the closest current distance metric and displacement as supplemental.
This is not direct numeric calibration to an experimental arena.

Actometer locomotor activity and threat-assay speed remain partial. The
simulator measures speed and distance-like output, but does not reproduce an
actometer or passing-shadow trial context.

## Implemented By G5 But Not Yet Validated For The Frozen Candidate

G5 implements analysis modules for:

- movement bouts,
- pause bouts,
- yaw rate and turn bouts,
- trajectory CSV export,
- optional virtual open-field occupancy.

Those modules require raw position and orientation arrays. Frozen E3/E4/E5 JSON
reports do not store those arrays, and G6 was not authorized to rerun
simulations. Therefore these endpoints are measurement-ready but not validated
for the frozen candidate.

## Not Supported

The following endpoint families are not supported by current frozen evidence:

- distance per movement / per-bout distance,
- angular velocity / time-resolved turning,
- centrophobism / center avoidance,
- negative geotaxis / SING,
- climbing behavior,
- stop durations / freezing / pause behavior,
- stimulus reactivity,
- proboscis extension response endpoints,
- tremor,
- biological treatment or rescue,
- inter-leg coordination phase or gait regularity,
- body height as a Parkinson phenotype.

Body height is measured in frozen reports and changed substantially in the
candidate, but it remains a simulation confound. It is not validated as a
biological Parkinson endpoint.

## Scientific Boundary

`SUPPORTED` in G6 means supported as a computational simulator phenotype under
the frozen evidence chain. It does not mean biological validation, statistical
significance, Parkinson's disease validation, dopamine equivalence, disease
severity mapping, mechanistic equivalence, or biological rescue.
