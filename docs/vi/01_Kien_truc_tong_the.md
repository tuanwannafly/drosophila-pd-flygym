# 2. Kiến trúc tổng thể

## Sơ đồ chính

```text
FlyGym / Scene JSON
        ↓
   Rollout Loader
        ↓
   Validation + QC
        ↓
   Workspace / Experiment Workspace
        ↓
      Digital Fly
 (body, skeleton, trajectory)
        ↓
 Digital Fly 3D Motion Engine
       (FK / pose / viewer)
        ↓
   Analysis + Statistics
        ↓
 Visualization + Reports
        ↓
       Export
        ↓
  Plugin Platform (extension boundary)
```

Plugin Platform là lớp mở rộng, không thay thế các bước hiện có. Plugin chỉ
nhận `PluginContext` và dữ liệu được host truyền vào. Context không chứa
đối tượng Workspace nội bộ.

## Các lớp web

- `workspace.js`: state của scene, selection, frame và playback.
- `experiment_workspace.js`: experiment, dataset, comparison, snapshot và
  registry legacy.
- `integration_workflow.js`: workflow import đến persistence.
- `analysis_pipeline.js`: feature graph, normalization, QC, outlier và cache.
- `statistical_engine.js`: thống kê mô tả, kiểm định, effect size, tương quan
  và report.
- `plugin_platform.js`: manifest, lifecycle, hook, capability, context và
  dependency checking.

## Tương thích

`ExperimentWorkspace.plugins` vẫn giữ `PluginRegistry` cũ. `pluginPlatform`
là API additive cho manifest-based plugin; hai API không bị trộn trạng thái.

Lớp release engineering nằm ngoài pipeline khoa học và cung cấp health scan,
module index, dependency graph, debug trace và release report. Các utility
này chỉ đọc source/configuration hoặc chạy operation do developer truyền vào.

Lớp `drosophila_pd.parkinson` nằm sau rollout và measurement: nó đọc
`RolloutData`, tính motor features, behavior timeline, computational index và
report. Lớp này không sở hữu FlyGym/MuJoCo state.

Lớp `drosophila_pd.scientific_validation` nằm sau analysis và đọc observed/
reference arrays. Nó tạo agreement metrics, reproducibility checks, benchmark,
figures và report mà không chạy lại simulation.
