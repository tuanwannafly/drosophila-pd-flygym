# Campaign Runtime

The V6 command surface is:

```text
python scripts/run_campaign.py discover
python scripts/run_campaign.py prepare
python scripts/run_campaign.py execute
python scripts/run_campaign.py status
python scripts/run_campaign.py report
python scripts/run_campaign.py bundle
```

The default campaign is the V5 `experimental_campaign_01_healthy_baseline`
planning package. Until real rollout data is curated under a dataset manifest,
`discover`, `prepare`, and `execute` report `WAITING_DATASET`.

The runtime output defaults to `results/execution/<campaign-id>`, which is
generated result material rather than frozen scientific evidence.
