# 15. Quản lý Dự án

Một project có thể lưu:

- tên, tag, status, notes và version;
- subjects và trials;
- experiment và analysis session;
- report, export và notebook liên quan.

Các method chính:

- `createProject()` và `updateProject()`;
- `addSubject()` và `addTrial()`;
- `addExperiment()`;
- `setFavorite()` và `browse()`;
- `dashboard()` để tổng hợp số lượng.

Model dùng `EntityStore` để giữ id, metadata, timestamps và JSON round-trip.
Các quan hệ project/subject/trial/experiment được kiểm tra khi tạo; trial
hoặc subject khác project sẽ bị từ chối.
