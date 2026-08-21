# 13. FAQ

## Epic 12 có chạy simulation không?

Không. Release tooling chỉ static-scan repository hoặc chạy callable do
developer truyền vào benchmark.

## Release report có thay đổi evidence không?

Không. Report mới nằm trong `docs/release_engineering/`; evidence và report
v1 trong `results/`/`dist/` vẫn được giữ nguyên.

## Plugin có được truy cập Workspace không?

Không trực tiếp. Host chỉ nên expose service hẹp qua `PluginContext`.

## `INFO` trong ProjectHealth có phải lỗi không?

Không nhất thiết. Các kiểm tra unused import/export và documentation coverage
là heuristic; chúng được báo cáo để review thủ công, không tự biến thành
failure.

## Có thể benchmark toàn bộ pipeline ngay không?

`BenchmarkSuite` hỗ trợ đủ category, nhưng operation phải do caller cung cấp.
Tooling không tự chạy FlyGym, MuJoCo hay tạo dữ liệu khoa học.

## Tài liệu nào là nguồn chuẩn?

Source code và `PROJECT_CONTEXT.md` là nguồn chuẩn. `docs/vi/` là tài liệu
giải thích đồng bộ, không thay thế API hoặc evidence.
