# Timeline Three.js

`TimelineController` chỉ quản lý DOM controls và gọi callback của viewer.
Frame hiện tại là state của `Viewer`; timeline không giữ một bản sao dữ liệu
animation và không parse JSON.

Với pose document, tổng số frame lấy từ `frame_count`. Với `DigitalFly3D`,
tổng số frame được suy ra từ các trajectory đã import. Khi seek, viewer render
frame tương ứng và callback có thể đồng bộ `Workspace.currentFrame` của Web App.

Timeline không điều phối FlyGym và không tạo dữ liệu frame mới.
