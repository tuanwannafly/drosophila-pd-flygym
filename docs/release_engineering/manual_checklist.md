# Manual Checklist

- [ ] Run `PYTHONPATH=src python scripts/generate_release_report.py`.
- [ ] Inspect `release.json`, `release.md`, and `release.html`.
- [ ] Confirm the source commit and compatibility matrix.
- [ ] Run `ProjectHealth` and review `INFO` heuristic findings.
- [ ] Build `ArchitectureSnapshot` and inspect module/API/dependency counts.
- [ ] Register caller-supplied operations for all benchmark stages.
- [ ] Run debug logger/timing/performance traces on a non-scientific smoke
      operation.
- [ ] Confirm no simulation, evidence regeneration, or frozen-file change.
