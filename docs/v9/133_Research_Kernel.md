# Research Kernel

`ResearchKernel` is the V9 orchestration boundary. It owns kernel lifecycle,
event persistence, service registration, resource indexing, and task scheduling.
It delegates dataset discovery and experiment execution to existing APIs.

The kernel creates operational outputs only. It never creates rollout data.
