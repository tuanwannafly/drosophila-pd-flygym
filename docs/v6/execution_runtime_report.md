# Execution Runtime Report

The local repository contains no executable dataset payload. The default
runtime therefore returns `WAITING_DATASET` and writes an operational JSON and
Markdown report under `results/execution/` when requested.

When a real manifest and its declared payloads are present, execution delegates
once to the existing `StudyOrchestrator`; no default simulation handler exists.
