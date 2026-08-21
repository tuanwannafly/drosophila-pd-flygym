# FlyGym Adapter

`drosophila_pd.flygym_adapter` là ranh giới tích hợp chính thức giữa project
và FlyGym 2.1.0. Người gọi dùng `FlyGymAdapter`, `FlyBuilder`, `WorldBuilder`
và `SimulationBuilder`, không cần import trực tiếp các lớp FlyGym trong mã
nghiên cứu.

Adapter chỉ tạo và điều phối đối tượng FlyGym đã được cấu hình. Nó không thay
đổi FlyGym, không fork FlyGym, không tạo rollout giả và không thêm thuật toán
Parkinson.

## Trạng thái cài đặt

Môi trường CI không cài FlyGym/MuJoCo mặc định. Các factory import lazy và sẽ
trả `FlyGymUnavailableError` với thông báo rõ ràng. Chạy mô phỏng thật trong
Python 3.12 với:

```powershell
python -m pip install -e ".[simulation]"
```

## Ranh giới an toàn

Adapter không gọi `add_joints()` và không gán `fly.skeleton`. Các bước
materialization và actuator vẫn thuộc pipeline canonical đã được kiểm chứng.

## Phạm vi khoa học

Rollout do adapter ghi là quan sát mô phỏng tính toán và metadata phần mềm.
Chúng không phải bằng chứng sinh học và không xác nhận bệnh Parkinson.
