# Version 2 Research Campaign Engine

The research campaign engine is the canonical Version 2 orchestration layer for
large computational behavior campaigns. It builds deterministic experiment
plans, tracks provenance, organizes artifacts, builds datasets, generates
figures, and verifies replay integrity.

It is additive to the frozen v1 repository and does not modify simulations,
controllers, perturbations, evidence JSON, notebooks, manuscript files, or
release artifacts.

Scientific scope: this is computational infrastructure only. It does not
validate Parkinson's disease biology, dopamine equivalence, disease severity, or
mechanistic causality.

Core modules:

- `campaign.py`: campaign config, matrix generation, scheduler, runner,
  checkpoint, resume, history, and manifest.
- `campaign_dataset.py`: dataset building, indexing, merging, and validation.
- `campaign_artifacts.py`: deterministic artifact directories and manifests.
- `campaign_figures.py`: publication-oriented figure and paper-asset factory.
- `campaign_provenance.py`: git, config, dataset, artifact, seed, software, and
  environment provenance.
- `campaign_reproducibility.py`: replay and hash verification.
- `scripts/research_campaign_cli.py`: command line entry point.

Canonical example:

```bash
python scripts/research_campaign_cli.py create \
  --config configs/v2/research_campaign/example_campaign.json \
  --output outputs/v2/example_campaign/campaign_plan.json
```
