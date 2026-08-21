# Integration Report

The complete path is implemented in `web/integration_workflow.js`. Successful imports return stage names, rollout, analysis, statistical summary, visualization payloads, exports, persistence verification and rollback status. Failed imports return a structured error and restore the pre-import workspace snapshot.

The validation suite checks module contracts. A Node runtime smoke test exercises valid import, batch analysis, persistence rollback, comparison, and benchmark behavior. Python repository tests do not run simulations.
