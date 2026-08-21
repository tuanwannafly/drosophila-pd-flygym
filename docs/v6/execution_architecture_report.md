# Execution Architecture Report

V6 introduces six focused execution modules: context, state, history, result,
artifact registry, and runtime. The CLI is a thin adapter. Dataset discovery
is the only gate before the existing `StudyOrchestrator`.

No simulation, rollout creation, scientific algorithm, Digital Twin, or
evidence file is modified.
