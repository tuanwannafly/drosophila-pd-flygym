# 4. Các module

| Module | Nhiệm vụ | Input | Output / phụ thuộc |
|---|---|---|---|
| `flygym_rollout.js` | Nhận dạng và chuẩn hóa rollout FlyGym | JSON rollout | rollout chuẩn hóa |
| `analysis_pipeline.js` | Chạy graph, normalization, QC và cache | rollout | analysis report |
| `statistical_engine.js` | Tính thống kê và tạo report | feature/value arrays | statistics/report |
| `integration_workflow.js` | Nối import đến persistence | rollout | workflow result |
| `experiment_workspace.js` | Quản lý experiment, dataset và snapshot | rollout/metadata | workspace state |
| `plugin_platform.js` | Lifecycle, manifest, hook và capability | plugin definition | plugin result/hook result |
| `verification_suite.js` | Kiểm chứng workflow và benchmark | rollout thật | verification report |
| `digital_fly.js` | Mô hình thực thể Fly và trajectory ownership | rollout đã chuẩn hóa | Digital Fly model |
| `digital_laboratory.js` | Đăng ký Digital Fly cùng project/trial metadata | Digital Fly + metadata | laboratory state |
| `digital_fly_3d.js` | Skeleton 3D, FK, pose, interpolation và metrics | Digital Fly + trajectory | 3D motion state |
| `digital_fly_3d_renderer.js` | Canvas perspective projection và overlay | 3D motion state | viewer pixels |
| `parkinson_export.js` | Export phân tích | analysis data | JSON/CSV/Markdown/HTML/SVG |
| `release_engineering.py` | Manifest, version, compatibility, migration và notes | repository | release metadata |
| `project_health.py` | Health scan tĩnh | repository | health checks |
| `developer_tooling.py` | API/module/dependency/hook explorers | repository | architecture snapshot |
| `debug_utils.py` | Event, timing, performance và diagnostic trace | caller events | diagnostic report |
| `benchmarking.py` | Benchmark operation do caller cung cấp | callables | benchmark report |

## Plugin examples

- `web/plugins/analysis_plugin.js`
- `web/plugins/statistics_plugin.js`
- `web/plugins/export_plugin.js`

Đây là extension boundary và ví dụ API, không phải kết quả khoa học mới.

CLI `scripts/generate_release_report.py` sinh report mới trong
`docs/release_engineering/`; không ghi đè report package v1 trong `dist/`.

Package Python `drosophila_pd.parkinson` là lớp hậu xử lý rollout cho
feature, behavior state, computational index, validation và report. Nó không
gọi simulation và không thay thế evidence v1.

Package `drosophila_pd.scientific_validation` là lớp đối chiếu rollout/reference,
reproducibility, benchmark và publication assets. Nó chỉ dùng input đã import.
