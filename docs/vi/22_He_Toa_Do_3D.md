# Hệ tọa độ 3D

Digital Fly dùng vector `[x, y, z]` và quaternion `[x, y, z, w]`. World
transform được tính từ root; Canvas viewer dùng phép chiếu perspective để hiển
thị trên mặt phẳng 2D. Ground, axes và display offsets phục vụ visualization,
không được đưa vào evidence hoặc metrics như dữ liệu quan sát.

Trajectory position được xem là world position khi channel cung cấp vector 3D.
Giả định này phải được ghi trong metadata/validation khi dùng cho phân tích.
