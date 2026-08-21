# SOP: Campaign Creation

1. Create a campaign definition from an approved protocol.
2. Record input dataset IDs, experiment IDs, configuration hashes, seeds, and
   expected outputs.
3. Check dependency order and output directory policy.
4. Review scientific scope before execution.
5. Save the manifest before any authorized run.

The campaign layer orchestrates caller-provided work; it must not invent
rollouts or silently alter a frozen experiment.
