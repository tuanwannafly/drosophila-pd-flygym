# Epic 17 — Scientific Validation Framework

Epic 17 là lớp validation hậu xử lý cho rollout và reference data đã import.
Nó không sửa FlyGym, simulation, evidence JSON hay tạo rollout mới.

## Thành phần

- `ReferenceDatasetManager`: đăng ký dataset, role, metadata, path và checksum.
- `compare_rollouts`: trajectory, orientation, COM, joints và feature mappings.
- `scientific_validation.statistics`: bootstrap, fold stability, sensitivity,
  outlier summary và effect size.
- `reproducibility`: output hash, repeated execution và seed consistency.
- `benchmark`: CPU, memory, scalability và caller-provided cache metrics.
- `visualization`: overlay, residual, heatmap, agreement và error figures.
- `generate_validation_report`: JSON/CSV/Markdown/HTML và publication indexes.

## Ranh giới

Framework chỉ đánh giá software agreement và reproducibility trên dữ liệu được
cung cấp. Không có biological validation, clinical diagnosis, disease severity,
mechanistic equivalence hay ngưỡng y khoa. Các role `PD` hoặc `Candidate` chỉ
là computational/data labels.

## CLI

```bash
python scripts/validate_scientific_pipeline.py \
  --observed path/to/observed.json \
  --reference path/to/reference.json \
  --output results/validation/epic_17
```

Lệnh trên chỉ đọc hai rollout đã có và ghi output vào thư mục do người dùng
chọn; không ghi đè các report frozen.
