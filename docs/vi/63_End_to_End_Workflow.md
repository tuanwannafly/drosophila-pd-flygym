# End-to-End Workflow

Luồng được kiểm tra bởi notebook 10:

```text
FlyGym
  -> Healthy_001
  -> Dataset Adapter
  -> Digital Fly / existing pipeline
  -> Analysis
  -> Statistics
  -> Computational PD
  -> Validation
  -> Reports
  -> Publication registration
```

Các module downstream hiện có được gọi qua CLI/orchestrator. Notebook không
copy hoặc thay đổi logic scientific.
