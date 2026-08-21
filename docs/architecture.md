# Architecture

Read the [repository architecture snapshot](repository_architecture.md) for
the current directory, package, dependency, API, CLI, and stability maps.

The repository has three boundaries:

1. the frozen V1 scientific/evidence path;
2. additive V2 post-processing and workflow services;
3. the Fly Studio browser presentation layer.

The boundaries meet through imported rollout/artifact formats and explicit
orchestration APIs. No V2 management layer silently changes frozen evidence.
