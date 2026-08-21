# 57. Workbench Nghiên cứu

Workbench là lớp điều phối giao diện cho các rollout và artifact đã được
import vào Fly Studio. Nó không chạy FlyGym, không tạo rollout và không đưa ra
kết luận sinh học.

Các vùng chính gồm dashboard, comparison, validation, figure, notebook,
bundle và layout. Dữ liệu hiển thị lấy từ `Workspace`, `ExperimentWorkspace`
và các module phân tích hiện có.

## Phạm vi

Workbench hỗ trợ quản lý một phiên nghiên cứu, ghi chú, tham chiếu figure,
kiểm tra report hiện có và đóng gói metadata. Mọi diễn giải Parkinson vẫn phải
tuân theo giới hạn của evidence và manuscript v1.0.0.
