# Architecture Report

Epic 12 adds a release-engineering layer below `src/drosophila_pd/` and keeps
the scientific pipeline unchanged.

| Component | Responsibility |
|---|---|
| `release_engineering.py` | Version metadata, compatibility, migration notes, manifest and notes rendering |
| `project_health.py` | Conservative static health checks |
| `developer_tooling.py` | Module/API/dependency/hook/architecture explorers |
| `debug_utils.py` | Structured events, timing, performance and diagnostics |
| `benchmarking.py` | Caller-supplied software operation benchmarks |
| `scripts/generate_release_report.py` | JSON/Markdown/HTML report generation |

The tools are additive, use the standard library, and do not import or
execute FlyGym simulation code during static reporting.
