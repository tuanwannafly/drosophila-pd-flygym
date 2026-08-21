# Điều khiển chuyển động 3D

Motion engine không điều khiển FlyGym. `DigitalFly3D.updateFrame(frame)` chỉ
đọc trajectory registry, lấy sample tại frame, áp dụng pose vào skeleton và
chạy FK. Joint scalar nếu có thể gắn tên sẽ được dùng quanh axis của joint;
channel không đủ thông tin sẽ được giữ nguyên và báo qua danh sách applied.

Interpolation hỗ trợ linear translation, Catmull-Rom translation, quaternion
slerp và blend nhiều pose. Đây là API hậu xử lý/hiển thị, không phải controller
simulation.
