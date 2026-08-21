# Discussion

## Computational findings

The frozen evidence is internally consistent with a staged computational
locomotion framework. Scaling joint-angle commands produced a graded reduction
in simulated displacement and speed, while the measured action magnitude
followed the commanded scale. Reducing CPG coupling had modest effects at
intermediate values and a much larger locomotion loss and yaw deviation at
zero coupling. The combined response surface showed mostly near-additive
speed and displacement changes, with more nonlinear directional effects.

Across five paired seeds, the frozen `0.8/0.75` candidate reduced displacement,
mean speed, and path length relative to its unperturbed pairs. Its action
magnitude was lower by approximately 20 percent. This direction was consistent
for displacement and speed in all tested seeds, while trajectory-efficiency
changes were mixed and absolute yaw change increased in four of five seeds.
Body height also changed substantially, so it remains an important confound
and phenotype component rather than a secondary detail.

E5 showed that explicit computational restoration along the motor axis and the
combined axis moved the primary endpoints toward the control in the tested
conditions. Coordination-only restoration was mixed. These observations
describe the behavior of the configured simulation and perturbation interfaces.

## Literature layer

E4 found directional qualitative concordance for selected adult walking speed
and distance endpoints, but not for every endpoint in scope. The resulting
classification is `PARTIAL_PHENOTYPE_CONCORDANCE`. This wording is deliberately
limited: agreement in a selected simulated endpoint direction does not show
that the computational proxy represents the biological cause of a phenotype.

## Candidate interpretation

The `motor_scale = 0.8`, `coupling_scale = 0.75` configuration is a leading
computational candidate for further validation because it has a reproducible
multi-seed locomotor-output reduction and a defined response in E5. It is not
designated as Parkinson's disease, dopamine depletion, neuron loss, disease
stage, or biological severity. The current evidence cannot select a final
disease model.

## What the evidence does not establish

The results do not establish a causal biological mechanism, a calibrated
mapping from simulation parameters to fly neurobiology, or biological rescue.
They also do not establish statistical significance. The most defensible
interpretation is that the repository provides a reproducible computational
phenotype framework whose proxies and endpoints remain to be biologically
grounded.

## Next scientific requirements

Before any disease-specific designation, the project needs literature-backed
definitions for the relevant fly phenotypes, measurements that are comparable
between simulation and experiment, a biological interpretation of controller
and actuator changes, and an analysis plan that specifies uncertainty and
replication independently of a desired outcome. Those requirements are outside
this frozen report package.
