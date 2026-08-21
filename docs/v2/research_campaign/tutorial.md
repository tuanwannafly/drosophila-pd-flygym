# Research Campaign Tutorial

Create a deterministic campaign plan:

```bash
python scripts/research_campaign_cli.py create \
  --config configs/v2/research_campaign/example_campaign.json \
  --output outputs/v2/example_campaign/campaign_plan.json
```

Run the infrastructure validation executor:

```bash
python scripts/research_campaign_cli.py execute \
  --config configs/v2/research_campaign/example_campaign.json \
  --output-dir outputs/v2/example_campaign
```

Generate figures without simulation:

```bash
python scripts/research_campaign_cli.py figures \
  --output-dir outputs/v2/example_campaign/figures
```

Build a summary report and paper asset folders:

```bash
python scripts/research_campaign_cli.py report \
  --output-dir outputs/v2/example_campaign/report
```

These commands validate the campaign plumbing only. Scientific rollouts should
be supplied by frozen or explicitly authorized simulation pipelines.
