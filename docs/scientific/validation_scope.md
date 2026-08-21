# G4 Biological Validation Scope

G4 is a post-release traceability layer. It maps biological endpoints curated in
G3 to currently available repository observables and records what is absent.
It does not rerun simulations, execute notebooks, alter frozen evidence, or
revise Release v1.0.0 conclusions.

## Boundary

The frozen scientific boundary is unchanged:

- The project is a computational and phenomenological locomotion framework.
- Milestone E4 remains `PARTIAL_PHENOTYPE_CONCORDANCE`.
- E4 is qualitative and direction-only.
- Milestone E5 remains computational reversibility only.
- No current result validates Parkinson's disease biology, dopamine depletion,
  neuron loss, disease severity, pharmacological rescue, mechanistic
  equivalence, or statistical significance.

## Support Levels

`SUPPORTED` means a repository observable exists and corresponds directly
enough for qualitative direction-only comparison under the frozen E4 rules.
Only adult walking speed / velocity / mean speed currently reaches this level,
through `mean_planar_speed_mm_s`.

`PARTIALLY_SUPPORTED` means a repository observable is related but not equivalent
to the biological endpoint. Covered or total moving distance maps best to
`planar_path_length_mm`, with `planar_displacement_mm` as supplemental context.
Actometer locomotor activity and threat-assay speed are also partial because
the assay apparatus or stimulus context is not represented.

`NOT_SUPPORTED` means the repository lacks the endpoint, or the available metric
must not be used as a substitute. This includes movement-bout distance, angular
velocity, centrophobism, negative geotaxis, vertical climbing, freezing or pause
duration, stimulus reactivity, PER endpoints, tremor, inter-leg coordination,
biological treatment rescue, and body height as a Parkinson endpoint.

## Currently Supported

The only fully supported biological endpoint family is adult walking speed /
velocity / mean speed, mapped to `mean_planar_speed_mm_s`. The mapping is
qualitative and direction-only. It is supported by the frozen E4 concordance
evidence and the G3 expanded literature inventory.

## Partially Supported

Distance-like locomotor-output endpoints are partially supported. Path length is
the primary repository observable for covered distance or total moving distance,
while displacement is supplemental. These mappings remain partial because the
repository does not match experimental arenas, durations, genotypes, tracking
protocols, or spontaneous activity conditions.

Threat-assay speed is also partial: speed exists, but passing-shadow stimulus
trials and response windows do not.

## Unsupported

The unsupported endpoint set is scientifically important. Most adult Drosophila
Parkinson locomotion studies in G3 use endpoints that the current frozen
flat-ground walking evidence does not measure, especially climbing, negative
geotaxis, bout structure, pauses, turning velocity, center avoidance, reactivity,
PER motor behavior, and tremor.

Body height is measured, but it is classified as a simulation confound and
posture descriptor only. It is not a supported Parkinson endpoint in the curated
adult locomotion literature.

## How To Use This Scope

Future milestones may use these files to choose new measurements, but support
levels must not be upgraded without new repository evidence and explicit
authorization. Biological claims require external experimental evidence and a
prespecified mapping bridge; simulation response alone is insufficient.
