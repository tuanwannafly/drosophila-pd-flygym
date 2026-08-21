# Normalization

`normalizeFeatureBundle` supports `global`, `rollout`, `experiment`, `joint`, and `bodyPart` scope labels. Z-score, min-max, and robust center/spread methods are available. `normalizeBatch` can calculate global parameters from a batch and apply them consistently.

Normalization is computational preprocessing. It does not alter frozen evidence and does not imply that a normalized feature has biological meaning beyond its source measurement.
