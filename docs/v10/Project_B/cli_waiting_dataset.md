# CLI and `WAITING_DATASET`

The existing read-only CLI remains authoritative:

```powershell
python scripts/dataset_cli.py status
python scripts/run_campaign.py discover
python scripts/experiment_runtime.py prepare
python scripts/kernel.py boot
```

With no approved PD dataset under the discovery roots, the expected state is
`WAITING_DATASET`. This is a correct stop condition, not a failed scientific
experiment. Project B adds no CLI implementation.
