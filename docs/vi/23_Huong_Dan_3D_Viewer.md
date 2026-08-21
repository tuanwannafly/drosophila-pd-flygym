# Hướng dẫn 3D Viewer

Khi import FlyGym rollout, App tạo `DigitalFly3D` và truyền model cho
`ViewportRenderer`. Viewer Canvas hỗ trợ:

- perspective projection, zoom và pan;
- right-drag hoặc Shift + middle-drag để orbit;
- double-click để focus node đang chọn;
- ground grid, coordinate axes, joint axes, COM, trajectory và skeleton overlay.

Scene JSON không có rollout vẫn giữ renderer cây 2D cũ. Viewer không gọi
FlyGym, không tạo trajectory và không thay đổi Workspace data.
