# Dataset Specifications

These specifications define intake contracts for future datasets. They do not
create `datasets/` payloads and do not designate any condition as a validated
Parkinson's disease model.

## Dataset types

| Type | Intended use | Scientific status |
| --- | --- | --- |
| Healthy | Unperturbed computational baseline | Frozen computational baseline |
| PD | Reserved label for a future computational PD-like condition | Not currently populated or biologically validated |
| Candidate | Frozen computational candidate comparisons | Computational candidate only |
| Control | Identity or control condition for paired analyses | Computational control |
| Validation | Reproducibility, robustness, or endpoint validation inputs | Validation artifacts only |
| Benchmark | Software/analysis performance inputs | Benchmark artifacts only |

Each type has a README and type-specific schema pointers. Shared policy is in
`reproducibility/dataset_policy.md`; the repository must not contain fabricated
payloads.
