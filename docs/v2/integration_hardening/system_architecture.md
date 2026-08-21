# System Architecture

Milestone 9 adds an integration adapter, not a replacement architecture. `IntegrationWorkflow` composes the existing rollout loader, rollout statistics, analysis pipeline, statistical engine, experiment workspace, visualization/export functions, and workspace persistence.

No adapter owns simulation state. The normalized rollout remains the handoff object between import and analysis stages.
