# Execution State

The explicit state machine is:

`WAITING_DATASET` -> `READY` -> `RUNNING` -> `VALIDATING` -> `EXPORTING` -> `COMPLETED`

`FAILED` and `CANCELLED` are terminal outcomes for the current request. A
failure may be returned to `READY` by a caller that explicitly retries after
correcting the external cause. No state transition starts a simulation.

Every transition is recorded in `ExecutionHistory` with a timestamp and
metadata. Invalid transitions raise an error rather than silently skipping a
stage.
