# Final Scientific Report Package

This directory contains the documentation package for the frozen computational
evidence through Milestone E6. It is a report of a reproducible Drosophila
locomotion simulation workflow and its evidence synthesis, not a claim that the
workflow is a validated Parkinson's disease model.

## Contents

- [final_report.md](final_report.md): assembled, submission-ready scientific
  manuscript.
- [methods.md](methods.md): computational design, controls, perturbation
  proxies, and analysis procedures.
- [results.md](results.md): frozen baseline, response-surface, robustness,
  concordance, and reversibility results.
- [discussion.md](discussion.md): interpretation within the evidence boundary.
- [limitations.md](limitations.md): scientific, computational, and
  reproducibility limitations.
- [reproducibility.md](reproducibility.md): environments, commands, commits,
  and evidence paths.
- [figure_captions.md](figure_captions.md): captions for the four E6 figures.
- [evidence_traceability.md](evidence_traceability.md): claim-to-artifact
  mapping for the report.

## Source of truth

The primary synthesis artifact is
`results/analysis/milestone_e6_synthesis.json`. Its eight upstream frozen JSON
reports, five generated CSV tables, and four generated figures are the source
for the statements in this package. Historical notebooks are retained as
research records but are not treated as the current implementation or as
independent validation of the frozen results.

E6 is an evidence-only synthesis stage. It reads frozen evidence, validates
provenance and hashes, and produces tables and figures. It does not run
FlyGym, MuJoCo, or new simulations. The known dirty Session 02 notebook was
excluded from synthesis changes and remains an out-of-scope historical file.

## Current boundary

The frozen evidence supports computational statements about simulated
locomotor output, parameter response, paired-seed robustness, qualitative
literature concordance, and computational reversibility. E4 remains
`PARTIAL_PHENOTYPE_CONCORDANCE`; E5 is computational reversibility only.

Nothing in this package establishes dopamine depletion, neuron loss, disease
severity, biological rescue, mechanistic equivalence, or statistical
significance. No condition is designated as validated Parkinson's disease.

## Rebuilding the synthesis

From the repository root, with the analysis dependencies available:

```bash
python scripts/run_evidence_synthesis.py \
  --config configs/analysis/milestone_e6.yaml \
  --output results/analysis/milestone_e6_synthesis.json
```

That command regenerates the evidence-only synthesis from the pinned upstream
reports. Reproducing the upstream simulation reports requires the documented
Colab environment and the exact input commits listed in
[reproducibility.md](reproducibility.md).
