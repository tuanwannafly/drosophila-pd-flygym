# V6 Execution Runtime

V6 adds an execution-only layer for a prepared research campaign. It discovers
dataset manifests, records execution state, delegates ready work to the
existing `StudyOrchestrator`, and registers artifacts.

The runtime does not run FlyGym, create rollout data, parse rollout arrays, or
make biological claims. With no real dataset payload present, the canonical
result is `WAITING_DATASET`.

See [the architecture](120_V6_Architecture.md) and [the manual checklist](manual_checklist.md).
