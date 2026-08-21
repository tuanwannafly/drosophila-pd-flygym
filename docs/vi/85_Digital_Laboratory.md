# Digital Laboratory

Digital Laboratory la lop tich hop cac module Web hien co: Dataset Browser,
Viewer, Timeline, Inspector, Charts, Analysis, Validation, Reports,
Publication va Plugins.

Lop tich hop khong thay the cac module nay va khong tao scientific pipeline
moi. `Workspace` van la source of truth cho frame, playback va selection.

## Luong su dung

```text
Dataset JSON
    -> Workspace
    -> Viewer + Timeline + Inspector
    -> Analysis/Validation/Reports
```

Viewer pose duoc nap tu `viewer_pose.json` thong qua Viewer hien co. Rollout
FlyGym duoc nap qua loader hien co va duoc chia se cho cac chart/analysis hien
co.

## Pham vi khoa hoc

Day la computational workspace. Giao dien khong chay simulation, khong thay
doi evidence frozen, va khong phat sinh khang dinh sinh hoc hay chan doan
Parkinson.
