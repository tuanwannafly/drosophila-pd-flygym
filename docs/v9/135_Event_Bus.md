# Research Bus

`ResearchBus` is an in-process publish/subscribe bus with durable `events.json`
output. Kernel lifecycle and task events use stable string names, including
`DATASET_READY`, `SESSION_CREATED`, `CAMPAIGN_STARTED`, `STUDY_COMPLETED`,
`PACKAGE_CREATED`, `ARCHIVED`, and `WAITING_DATASET`.

`timeline.json` is a numbered projection of the same event history.
