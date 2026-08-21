# Web Viewer

Web Viewer hien tai dung ES modules trong `web/`. Viewer pose moi o
`web/viewer/` la skeleton architecture doc lap, chua duoc noi vao ung dung
chinh va khong dung Three.js.

Luong du kien:

`viewer_pose.json` -> `pose_loader` -> `skeleton_animator` -> `scene_builder`
-> `trajectory_renderer` -> `digital_fly_viewer`.

Camera va playback chi la transform/state boundary. Du lieu phai den tu pose
document da import; khong tao pose hoac rollout gia.
