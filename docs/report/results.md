# Results

All values below are taken from frozen evidence or the generated E6 tables.
They describe simulation outputs and software reproducibility only.

## Unperturbed baseline

The Milestone C unperturbed baseline passed its Colab integration checks at
Python 3.12.13, FlyGym 2.1.0, and MuJoCo 3.9.0. The 0.5 s run used a 0.0001 s
time step and 5000 steps. It compiled 42 position actuators and 6 adhesion
actuators (`nu = 48`).

| Metric | Frozen value |
| --- | ---: |
| Planar displacement (mm) | 6.284186050286936 |
| Mean planar speed (mm/s) | 12.568372100573873 |
| Yaw change (rad) | 0.2342730946151257 |
| Thorax height minimum (mm) | 0.7660532202481788 |
| Thorax height mean (mm) | 0.946592192150494 |
| Thorax height final (mm) | 1.0115140447050612 |

All required observations and derived metrics were finite. This is an
unperturbed simulation baseline, not biological validation.

## E1 parameter-response surfaces

The compact response table below reports the E1 control and the main locomotor
outputs. Relative changes are relative to the scale-1.0 control in the same
family. Path length and trajectory efficiency were not present in the E1
source report and are therefore intentionally blank in the generated E1
table.

### Motor-vigor proxy

| Scale | Displacement mm | Speed mm/s | Yaw rad | Height mean mm | Height min mm | Height range mm | Action abs mean | Relative displacement |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1.00 | 6.2841860503 | 12.5683721006 | 0.2342730946 | 0.9465921922 | 0.7660532202 | 0.4241419610 | 1.0243701362 | 0.0000% |
| 0.90 | 5.7781947167 | 11.5563894334 | 0.2590417418 | 1.1725515871 | 0.9752236333 | 0.4027986331 | 0.9219331226 | -8.0518% |
| 0.80 | 5.6127365828 | 11.2254731657 | 0.2648836253 | 1.4787535043 | 1.1578504429 | 0.4230394666 | 0.8194961090 | -10.6847% |
| 0.70 | 5.2680506122 | 10.5361012245 | 0.1185962496 | 1.7640121539 | 1.1578504429 | 0.6849080350 | 0.7170590953 | -16.1697% |
| 0.60 | 4.6653476524 | 9.3306953048 | 0.1214983384 | 2.0254362306 | 1.1578504429 | 1.1738072615 | 0.6146220817 | -25.7605% |

Displacement and speed decreased across the motor scale sequence, and action
magnitude followed the commanded scale exactly. Height mean and range changed
nonlinearly. Yaw did not change monotonically.

### Coordination proxy

| Coupling | Displacement mm | Speed mm/s | Yaw rad | Height mean mm | Height min mm | Height range mm | Action abs mean | Relative displacement |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1.00 | 6.2841860503 | 12.5683721006 | 0.2342730946 | 0.9465921922 | 0.7660532202 | 0.4241419610 | 1.0243701362 | 0.0000% |
| 0.75 | 6.2172362770 | 12.4344725541 | 0.2912150604 | 0.9466709444 | 0.7829816301 | 0.4081431926 | 1.0243119640 | -1.0654% |
| 0.50 | 6.1055378540 | 12.2110757079 | 0.3313098729 | 0.9564334845 | 0.7780077465 | 0.4141548997 | 1.0244046906 | -2.8428% |
| 0.25 | 5.8643592546 | 11.7287185093 | 0.6723370956 | 0.9533110557 | 0.7374134292 | 0.4560225964 | 1.0243975186 | -6.6807% |
| 0.00 | 3.4054361974 | 6.8108723947 | 2.2263880793 | 0.9526676460 | 0.6583795628 | 0.5364396391 | 1.0239380324 | -45.8094% |

Intermediate coupling reductions had modest effects on displacement and speed.
Near-zero coupling caused a large locomotion loss and large yaw deviation.
Action magnitude stayed essentially unchanged because this proxy changes CPG
coupling rather than global action amplitude.

## E2 combined conditions

| Condition | Motor | Coupling | Displacement mm | Speed mm/s | Yaw rad | Height mean mm | Action abs mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Control | 1.00 | 1.00 | 6.2841860503 | 12.5683721006 | 0.2342730946 | 0.9465921922 | 1.0243701362 |
| Motor only | 0.80 | 1.00 | 5.6127365828 | 11.2254731657 | 0.2648836253 | 1.4787535043 | 0.8194961090 |
| Motor only | 0.70 | 1.00 | 5.2680506122 | 10.5361012245 | 0.1185962496 | 1.7640121539 | 0.7170590953 |
| Motor only | 0.60 | 1.00 | 4.6653476524 | 9.3306953048 | 0.1214983384 | 2.0254362306 | 0.6146220817 |
| Coordination only | 1.00 | 0.75 | 6.2172362770 | 12.4344725541 | 0.2912150604 | 0.9466709444 | 1.0243119640 |
| Coordination only | 1.00 | 0.50 | 6.1055378540 | 12.2110757079 | 0.3313098729 | 0.9564334845 | 1.0244046906 |
| Combined | 0.80 | 0.75 | 5.5134994898 | 11.0269989796 | 0.3025992185 | 1.4789059644 | 0.8194495712 |
| Combined | 0.70 | 0.75 | 5.1365318532 | 10.2730637063 | 0.1566392864 | 1.7535528444 | 0.7170183748 |
| Combined | 0.70 | 0.50 | 5.0294797156 | 10.0589594313 | 0.2533262746 | 1.7421945484 | 0.7170832834 |

The combined `0.8/0.75` condition is the frozen computational candidate for
further validation only. It is not a validated disease condition.

For displacement and speed, combined responses were mostly close to the sum
of the corresponding single-proxy changes. Yaw effects were more nonlinear:
the direction and magnitude of yaw did not follow a simple additive rule.

## E3 candidate robustness

The frozen candidate was tested for 1.0 s at seeds 0 through 4, with a fresh
fly, world, and simulation per condition and the same seed within each pair.
All five displacement deltas and all five speed deltas were negative.

| Aggregate metric | Baseline mean | Candidate mean | Relative delta |
| --- | ---: | ---: | ---: |
| Displacement (mm) | 13.751281674590993 | 12.302040063313584 | -10.54% |
| Mean speed (mm/s) | 13.751281674590993 | 12.302040063313584 | -10.54% |
| Path length (mm) | 19.31485503067457 | 17.308442670909542 | -10.39% |
| Trajectory efficiency | 0.7119806020699851 | 0.7107636180753024 | -0.16% |
| Joint action absolute mean | 1.0256368082597096 | 0.820559121832831 | -20.00% |
| Body height mean (mm) | 0.9465522152698778 | 1.4910686043526398 | not normalized |
| Absolute yaw change (rad) | 0.10385794490113649 | 0.21120580249246884 | not normalized |

Per-seed speed/displacement deltas were `-1.3449545432`, `-1.4705577755`,
`-1.5704411834`, `-1.4901033657`, and `-1.3701511886` in the same units as
the corresponding metric. Path-length deltas were `-2.1411832110`,
`-2.0026138381`, `-1.9331712681`, `-2.1415643132`, and `-1.8135291685` mm.

The E3 classification `ROBUST` means computational/software robustness under
these tested seeds only.

## E4 qualitative concordance

E4 classified the comparison as `PARTIAL_PHENOTYPE_CONCORDANCE`. Four selected
literature endpoints were directionally concordant, three were not comparable,
and one was insufficiently specified. This is a qualitative evidence layer,
not a biological validation score.

## E5 computational reversibility

E5 used the frozen candidate as the impaired reference and tested computational
partial restoration. The primary endpoint results were:

| Restoration | Speed mean | Speed recovery | Path mean | Path recovery | Classification |
| --- | ---: | ---: | ---: | ---: | --- |
| Motor partial (`0.9/0.75`) | 12.7985542632 | 0.3426027765 | 18.0648372438 | 0.3769885932 | Directionally rescued |
| Coordination partial (`0.8/0.875`) | 12.3863834838 | 0.0581983154 | 17.3230166277 | 0.0072636897 | Mixed |
| Combined partial (`0.9/0.875`) | 12.8239824043 | 0.3601486025 | 18.0186997760 | 0.3539935854 | Directionally rescued |
| Full computational reference (`1.0/1.0`) | 13.7512816746 | 1.0 | 19.3148550307 | 1.0 | Reference |

These are computational endpoint movements toward a control configuration.
They are not biological rescue or treatment-response measurements.

## E6 synthesis

The E6 synthesis passed all 56 checks. It represented eight upstream frozen
reports, verified the SHA-256 input manifest, and generated four figures and
five CSV tables. It preserved E4 as `PARTIAL_PHENOTYPE_CONCORDANCE` and E5 as
computational reversibility only. No statistical-significance claim was added.
