# Statistical Analysis Engine

The Statistical Engine is a pure post-processing layer for finite numeric arrays and existing analytics outputs. It does not mutate rollouts, run simulation, or update UI state.

The modules are separated by responsibility:

- descriptive statistics and distributions;
- deterministic bootstrap and jackknife resampling;
- hypothesis-test procedures;
- effect sizes and multiple-comparison corrections;
- correlation and regression;
- assumption and data validation;
- report serialization and benchmark timing.

`StatisticalEngine` provides the stable orchestration API while individual functions remain importable for focused use.
