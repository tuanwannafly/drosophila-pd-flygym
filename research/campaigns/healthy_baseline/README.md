# Experimental Campaign 01: Healthy Baseline

This directory contains the planning package for the first real Healthy
campaign. It contains protocols, schemas, templates, and a deterministic
experiment matrix only.

**Planning status:** no rollout has been executed and no scientific dataset has
been created.

## Package

- `manifest.schema.json` - JSON Schema for a future dataset manifest.
- `dataset_manifest.template.json` - empty planning manifest.
- `campaign.yaml` - campaign metadata and execution guard.
- `experiment_matrix.csv` - Healthy_001 through Healthy_100 plan.
- `experiment_plan.md` - matrix semantics and expected artifacts.
- `metadata.template.yaml` - per-experiment metadata template.
- `checksum.template.json` - checksum manifest template.
- `research_notebook_template.ipynb` - markdown-only execution record template.
- `publication/healthy_baseline/` - empty publication-asset layout anchors.

The first execution must use an explicitly approved protocol, a new output
path, the documented environment, and a fresh provenance record. This package
does not change the frozen baseline evidence.
