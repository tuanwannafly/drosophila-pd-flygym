# Experiment Runtime

`ExperimentRuntime` is the V8 orchestration boundary. Its commands are
`prepare`, `bind`, `run`, `status`, `summary`, and `archive`.

`run` discovers the V7 dataset adapter result once for that invocation. If the
result is not `READY`, it persists a waiting session and does not call any
downstream pipeline. If it is `READY`, it constructs an existing
`StudyRequest` and calls `StudyOrchestrator` exactly as the integration point.
