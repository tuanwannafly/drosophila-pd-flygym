# Epic 12 — Release Engineering, Developer Experience và tài liệu tiếng Việt

## Mục tiêu

Epic 12 bổ sung lớp maintainability và release tooling additive. Không thêm
Analytics, Statistics, Parkinson Engine hoặc simulation behavior mới.

## Thành phần

- `ReleaseManifest`, `VersionMetadata`, `CompatibilityMatrix` và
  `MigrationNotes`;
- `ProjectHealth` cho missing/duplicate/unused/dead plugin/circular/config/docs
  checks;
- `ModuleIndex`, `APIExplorer`, `DependencyGraphGenerator`, `HookExplorer`,
  `PluginRegistryViewer`, `ArchitectureSnapshot`;
- `DebugLogger`, `StructuredEventLog`, `TimingTrace`, `PerformanceTrace` và
  `DiagnosticReport`;
- `BenchmarkSuite` cho Import, Workspace, Plugin, Analysis, Statistics,
  Comparison, Export và Verification;
- `scripts/generate_release_report.py` tạo `release.json`, `release.md`,
  `release.html` trong `docs/release_engineering/`.

## Nguyên tắc không phá vỡ

- không sửa simulation, FlyGym, evidence, paper, notebooks hoặc artifact v1;
- không đổi public API hiện tại;
- tooling không chạy simulation tự động;
- benchmark không được coi là scientific evidence;
- heuristic health findings phải được review thủ công.

## Validation

```bash
python -m compileall -q src scripts tests
PYTHONPATH=src pytest -q -rs -p no:cacheprovider
git diff --check
```

## Manual workflow

1. Chạy release report generator.
2. Đọc health summary và architecture snapshot.
3. Đăng ký operation thật nếu cần benchmark.
4. Kiểm tra debug report không chứa secret/raw artifact lớn.
5. Xác nhận `git diff` không có file frozen trước commit.
