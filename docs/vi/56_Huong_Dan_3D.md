# 56. Hướng dẫn phòng thí nghiệm 3D

1. Mở Fly Studio Web và nạp một rollout JSON tương thích.
2. Chọn một body part trong Scene Tree hoặc nhấp trực tiếp vào mesh/joint.
3. Dùng camera preset, orbit, pan và zoom để quan sát.
4. Bật overlay cần kiểm tra; các overlay không có dữ liệu sẽ không tự tạo ra.
5. Dùng Play/Pause/Stop và timeline để xem frame đã import.
6. Với nhiều experiment, chọn các mục trong Experiment Workspace rồi dùng
   Comparison Viewer để xem trajectory đồng bộ.
7. Xuất PNG/SVG nếu cần lưu hình trình bày; kết quả khoa học vẫn lấy từ pipeline
   phân tích và evidence đã được version-control.

## Giới hạn

Đây là lớp trực quan hóa và tương tác. Nó không thay đổi simulation, không chạy
FlyGym, không chọn tham số bệnh và không cung cấp chẩn đoán Parkinson.
