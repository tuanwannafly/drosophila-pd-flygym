# State Management

`Workspace` quan ly:

- `currentFrame`, `totalFrames`, `currentTime`
- `playbackState`
- rollout va animation frames
- `selectedNode` va `selectedKeyframe`

`DashboardState` chi giu trang thai UI nho nhu tab dang mo va loi hien thi.
Moi snapshot cua DashboardState doc frame/playback/selection truc tiep tu
Workspace, khong tao state khoa hoc trung lap.

Khi Timeline thay doi frame, Workspace phat event. Viewer, Inspector,
Behavior Timeline, Charts va status bar cap nhat tu event do.
