# V8 Scientific Experiment Runtime

V8 provides session-based orchestration for experiments over real datasets
discovered by the V7 adapter. It persists lifecycle state and delegates ready
work to the existing `StudyOrchestrator`.

It does not add analysis, statistics, validation, Digital Twin, dashboard, or
simulation logic. With no dataset present, the runtime stops at
`WAITING_DATASET`.
