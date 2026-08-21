# 72. Kiến trúc Milestone 3

Luồng quản trị:

```text
Dataset Catalog -> Experiment Queue -> Existing Pipeline Handlers
        |                 |                    |
        +-> Artifact Manager -> Reproducibility Center
        +-> Benchmark Center -> Project Health Monitor
        +-> Publication Builder -> Automation CLI
```

Milestone 3 là lớp orchestration và reproducibility. Nó tái sử dụng các
module V2 hiện có, giữ nguyên simulation/evidence, và không thêm thuật toán
Parkinson. Mọi dữ liệu phải đến từ rollout hoặc artifact do caller cung cấp.
