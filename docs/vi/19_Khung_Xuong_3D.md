# Khung xương 3D

`Skeleton3D` gồm `Bone3D` và `Joint3D`. Mỗi bone có id, parent, children,
local transform và world transform. Transform dùng translation 3 chiều và
quaternion chuẩn hóa.

Hierarchy mặc định gồm Fly, Body, Thorax, Abdomen, Head, hai Wing và sáu leg
nodes. Đây là cấu trúc dữ liệu/hiển thị, không phải tuyên bố rằng mọi rollout
đều chứa đủ các kênh giải phẫu đó.
