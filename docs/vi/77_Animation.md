# Animation trong Viewer

`JointAnimator` đọc các frame từ `viewer_pose.json` và nội suy quaternion khi
frame yêu cầu là số thực. Rollout FlyGym được cập nhật qua
`DigitalFly3D.updateFrame(frame)`, vì vậy viewer dùng đúng trajectory đã import.

Playback dùng một vòng `requestAnimationFrame` duy nhất trong `viewer.js`.
Các trạng thái Play, Pause và Stop chỉ điều khiển viewer. Không có scheduler
simulation, không thay đổi controller FlyGym và không tự động chạy simulation.

Tốc độ và Loop là tùy chọn trình bày. Frame slider luôn có thể seek trực tiếp.
