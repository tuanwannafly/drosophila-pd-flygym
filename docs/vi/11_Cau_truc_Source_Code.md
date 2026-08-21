# 12. Cấu trúc Source Code

```text
src/drosophila_pd/
├── anatomy/          # FlyGym anatomy và mapping audit
├── analysis/         # Evidence-only analysis
├── assays/           # Behavioral assays
├── behavior_platform/ # Dataset, feature và AI platform
├── controllers/      # Controller interfaces
├── experiments/      # Experiment orchestration
├── flystudio/        # Fly Studio Python support
├── metrics/          # Locomotion/gait metrics
├── perturbations/    # Explicit computational perturbations
├── benchmarking.py   # Generic operation benchmark
├── debug_utils.py    # Developer diagnostics
├── developer_tooling.py
├── project_health.py
└── release_engineering.py

web/
├── workspace.js                # Web workspace source of truth
├── experiment_workspace.js     # Experiment/dataset workspace
├── integration_workflow.js     # End-to-end web workflow
├── plugin_platform.js          # Manifest-based plugin platform
├── verification_suite.js       # Verification adapter
└── plugins/                    # Plugin examples
```

`scripts/` chứa CLI, `tests/` chứa regression/contract tests, `docs/` chứa
tài liệu và report. `dist/` là artifact release đã đóng băng, không được dùng
làm thư mục output cho tooling mới.
