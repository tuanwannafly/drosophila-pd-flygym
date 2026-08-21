# Three.js Digital Fly Viewer

Viewer Three.js là lớp trình bày cho rollout đã được import. Viewer không chạy
FlyGym, không thay đổi dữ liệu rollout và không thay thế các module phân tích.

`web/viewer/viewer.js` là composition root. Các thành phần scene, mesh,
skeleton, trajectory, camera và timeline được tạo tại đây. Three.js được nạp
từ CDN phiên bản cố định trong import map của `web/index.html`.

Khi App nhận `DigitalFly3D`, Canvas viewer cũ được ẩn và viewer Three.js được
hiển thị. Với scene JSON thông thường, Canvas viewer cũ vẫn được dùng.

## Phạm vi

- Mesh hiển thị là hình học trình bày mặc định, không phải dữ liệu giải phẫu.
- Skeleton, COM và trajectory chỉ được vẽ khi rollout cung cấp dữ liệu tương ứng.
- Viewer không tạo rollout, không suy luận bệnh học và không thay đổi evidence.
