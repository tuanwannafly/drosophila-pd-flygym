# Sprint 1 experiment report

The runner supports one job and deterministic sequential batches. Each job
records status, attempts, stage summaries, configuration hash, git commit,
artifact hashes, timestamps, structured JSONL logs, and an error report on
failure.

The implementation does not provide a default simulation pipeline. This is an
intentional safety boundary: a successful real run requires explicit handlers
for rollout, Digital Fly, 3D motion, analysis, computational PD, scientific
validation, and publication export.
