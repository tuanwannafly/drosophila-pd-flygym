# 21. Trajectory và Digital Fly

Khi rollout có channel vô hướng hoặc vector, model tạo record trajectory tương
ứng dưới registry của Digital Fly. Channel dạng named-series tạo một record cho
mỗi tên. Mỗi record giữ `flyId`, metadata channel và binding như
`thorax:thorax` hoặc `joint:left_front`.

Các channel không có component hình thái riêng vẫn được gắn vào `motion`; điều
này giữ dữ liệu quan sát được mà không suy đoán cấu trúc sinh học. Channel vắng
mặt không được tạo placeholder.

`validate()` kiểm tra ownership của mọi trajectory và báo các record chưa có
binding. Kết quả là kiểm tra phần mềm đối với dữ liệu đã nhập, không phải kiểm
định sinh học.
