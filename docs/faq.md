# FAQ

## Does this repository validate Parkinson's disease?

No. It is computational simulation and analysis software. The frozen E4 result
is qualitative `PARTIAL_PHENOTYPE_CONCORDANCE` only.

## Where is the canonical manuscript?

`docs/report/final_report.md` is the source. The packaged deliverables are in
`dist/` and are indexed by `dist/final_report_manifest.json`.

## Can I run FlyGym locally?

Only with the documented Python 3.12, FlyGym 2.1.0, and MuJoCo 3.9.0
environment. Google Colab is the recorded execution environment.

## Where should new reusable logic go?

In `src/drosophila_pd/`, with a focused test and documentation. Keep notebooks
as interfaces or historical records rather than the only implementation.
