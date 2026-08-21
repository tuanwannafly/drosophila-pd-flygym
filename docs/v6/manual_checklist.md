# Manual Checklist

- [x] `python scripts/run_campaign.py discover` reports `WAITING_DATASET` in the current checkout.
- [x] Planning-only V5 templates do not unlock execution.
- [x] Missing payloads do not invoke downstream orchestration.
- [ ] Place an approved real dataset under a manifest and verify `READY`.
- [ ] Run `python scripts/run_campaign.py execute` against that approved dataset.
- [ ] Verify the downstream study manifest, validation output, and research package.
- [ ] Review hashes and provenance before scientific use.

The unchecked items require a real curated dataset and are intentionally not
performed by this milestone.
