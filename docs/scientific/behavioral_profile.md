# G8 Behavioral Profile

Phase G8 was intended to validate additional behavioral phenotypes using the
G7 measurement-enabled evidence package and the G5 measurement modules.

In this checkout, no G7 measurement-enabled evidence package was present under
`results/validation/g7_measurement_enabled_evidence_refresh/` or elsewhere
under `results/`. Therefore G8 does not upgrade any extended endpoint from
measurement capability to validated computational evidence.

## Current Supported Profile

The frozen computational candidate remains characterized by the G6 profile:

- reduced mean planar speed is supported as a qualitative computational
  phenotype;
- reduced distance-like locomotor output is partially supported;
- run-level yaw and body-height changes remain important computational
  observations and confounds;
- no Parkinson's disease validation, dopamine equivalence, disease-severity
  mapping, biological rescue claim, or statistical-significance claim is made.

## Extended Endpoint Status

The following endpoints are implemented or partly represented by G5 analysis
modules, but are not validated for the frozen candidate in this checkout:

- walking bouts;
- pause bouts;
- pause duration;
- walking duty cycle;
- yaw rate;
- turn bouts;
- cumulative turning;
- left/right turning asymmetry;
- open-field exploration metrics.

The reason is evidentiary rather than architectural: these endpoints require
G7 per-rollout trajectory, heading, speed, yaw-rate, bout, and measurement
summary outputs. Those outputs were not available locally during G8.

## Scientific Boundary

Measurement availability is not biological evidence. Any future G8 refresh must
continue to separate:

- computational observables from biological phenotypes;
- FlatGroundWorld trajectory summaries from experimental open-field assays;
- pause or turn segmentation from validated freezing, tremor, or gait assays;
- computational candidate behavior from Parkinson's disease validation.
