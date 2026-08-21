# 51. Trình xem 3D

Fly Studio dùng Canvas 2D để trình bày mô hình Digital Fly 3D đã được dựng từ
rollout được import. Renderer không tạo rollout, không gọi FlyGym và không thay
đổi dữ liệu mô phỏng.

## Điều khiển

- Chọn Perspective hoặc Orthographic.
- Chọn preset Front, Back, Left, Right, Top, Bottom hoặc Isometric.
- Cuộn chuột để zoom; giữ chuột giữa để pan; giữ Shift và chuột giữa, hoặc
  chuột phải, để orbit.
- Chọn Focus Selected để đưa body part đang chọn vào tâm.
- Nhấn Reset View để trở về camera mặc định.

## Nguồn dữ liệu

`DigitalFly3D` sở hữu skeleton và đọc các trajectory đã chuẩn hóa từ
`FlyGymRolloutLoader`. Mesh chỉ là hình học hiển thị đơn giản quanh các
transform đã quan sát.
