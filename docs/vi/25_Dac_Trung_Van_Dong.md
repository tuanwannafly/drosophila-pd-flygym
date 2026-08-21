# Đặc trưng vận động

Các đặc trưng được tính trực tiếp từ trajectory, orientation, COM, joint và
adhesion arrays có trong `RolloutData`. Danh mục gồm vận tốc đi bộ, vận tốc
stride khi có dữ liệu, cadence khi metadata cung cấp, gia tốc, vận tốc/gia tốc
góc, displacement và ổn định COM, ổn định heading, turning rate, curvature,
entropy đường đi, dao động/sway thân, ROM và đạo hàm joint, đối xứng trái/phải,
chuyển động wing/head khi series tương ứng tồn tại.

Đặc trưng không có dữ liệu đầu vào được ghi là `null` và `available=false`.
Không có giá trị mặc định giả. Đây là quy tắc quan trọng để phân biệt thiếu
dữ liệu với kết quả bằng không.
