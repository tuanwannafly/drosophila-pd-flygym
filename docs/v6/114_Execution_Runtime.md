# Execution Runtime

`drosophila_pd.research_execution.ExecutionRuntime` is the narrow V6
orchestration boundary. It receives an `ExecutionContext`, discovers dataset
manifests, and exposes `discover`, `prepare`, `execute`, `status`, `report`,
and `bundle` operations.

`execute` stops before downstream work when no executable manifest has a
declared, existing payload. This produces `WAITING_DATASET` and two local
execution reports. It does not create a substitute dataset.

When a real dataset is available, the runtime constructs the existing
`StudyRequest` and delegates to `StudyOrchestrator`. It does not implement
analysis, statistics, computational-PD, validation, publication, or
simulation logic.
