# 18. Mô hình Digital Fly

Digital Fly là mô hình dữ liệu đại diện cho một thực thể ruồi tính toán được
tạo từ rollout đã chuẩn hóa. Mô hình gom các thành phần hình thái và chuyển
động dưới một `flyId` duy nhất để các trajectory không bị rời khỏi thực thể.

## Thành phần

- `body` và `bodySegments`: hierarchy các phần thân;
- `skeleton` và `joints`: hierarchy xương và khớp quan sát được;
- `wings`, `legs`, `head`, `com`, `orientation`, `pose`, `motion`;
- `parkinsonState`: metadata tính toán, mặc định `unassigned` và không mang
  diễn giải sinh học;
- `TrajectoryRegistry`: registry bảo đảm mỗi record có `flyId` của Digital Fly.

Định nghĩa nằm trong `web/digital_fly.js`. Model chỉ biểu diễn dữ liệu do caller
cung cấp; nó không gọi FlyGym, không sửa rollout và không tạo dữ liệu khoa học.
