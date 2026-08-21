# CLI Guide

Scripts are grouped in the [CLI inventory](repository_architecture.md#cli-inventory).
Every script can be inspected with `--help` where supported. Use repository
paths for configuration and output so provenance remains readable.

Simulation commands are opt-in and environment-dependent. Metadata-only
commands such as automation, campaign, study, report, and validation commands
operate on caller-provided files and must not be treated as data generators.
