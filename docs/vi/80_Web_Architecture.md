# Kiến trúc Web Viewer

Luồng chính:

```text
JSONLoader / FlyGymRolloutLoader
        -> DigitalFly / DigitalFly3D
        -> Viewer
        -> Scene + Mesh + Skeleton + Trajectory + Camera
```

`Viewer` là composition root của lớp Three.js. `DigitalFlyScene` quản lý
ground, grid, axes và lighting; `DigitalFlyMesh`, `SkeletonRenderer` và
`TrajectoryRenderer` chỉ nhận dữ liệu đã có; `CameraController` chỉ thay đổi
transform camera; `TimelineController` chỉ phát sinh lệnh UI.

Canvas `ViewportRenderer` vẫn được giữ cho backward compatibility. App chọn
renderer theo loại dữ liệu: rollout FlyGym dùng Three.js viewer, scene JSON
thông thường dùng Canvas. Không có thay đổi ở FlyGym, MuJoCo, simulation,
analysis, validation hay evidence.
