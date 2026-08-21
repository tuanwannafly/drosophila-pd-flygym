# Future Candidates for Phase G2

These are traceability and research-interface candidates only. They are not
new simulation milestones and do not designate a biological condition.

## Candidate Work

1. Add a machine-readable block manifest for each historical notebook with
   notebook hash, cell index, block label, and classification. This would
   make the current YAML/CSV inventory checkable without parsing notebook
   prose.
2. Add a provenance checker that relates a frozen evidence report to its
   canonical runner commit, environment fields, and expected output schema.
   It should report missing links rather than infer them.
3. Add an artifact graph for the manuscript package: canonical source,
   evidence JSON, figures/tables, report section, and release artifact.
4. Create thin, fresh-runtime Colab execution notebooks only for canonical
   commands that already exist. The notebook should call repository scripts
   and display their JSON; it should not contain a second implementation.
5. Record the Session 02 attachment/sensor diagnostic as a short API note if
   future work needs ground-contact observations. Any change to sensor
   configuration would require a new explicitly scoped experiment.
6. Inventory absent Sessions 03-10 as repository gaps and define a policy for
   registering future notebooks when they are added.

## Out of Scope for G2 Inventory Work

- Re-running FlyGym or MuJoCo simulations.
- Reconstructing discarded debug cells as production code.
- Adding Parkinson's terminology, biological severity, dopamine mappings, or
  mechanistic claims.
- Modifying the protected Session 02 notebook or any frozen release artifact.
