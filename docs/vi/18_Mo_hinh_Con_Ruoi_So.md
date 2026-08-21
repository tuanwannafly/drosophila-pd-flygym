# Mô hình Con Ruồi Số 3D

Epic 15 mở rộng `DigitalFly` thành lớp `DigitalFly3D`. Object 3D giữ tham chiếu
đến Digital Fly owner và dùng đúng trajectory đã được `FlyGymRolloutLoader`
chuẩn hóa. Không có rollout mới hoặc dữ liệu mô phỏng giả được tạo trong lớp
này.

Các giá trị display offset trong skeleton chỉ là bố cục hiển thị mặc định. Khi
trajectory thật có vị trí, vị trí đó được ưu tiên; metrics chỉ dùng state có
dữ liệu đầu vào tương ứng.
