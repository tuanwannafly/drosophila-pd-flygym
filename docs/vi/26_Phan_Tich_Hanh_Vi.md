# Phân tích hành vi

Behavior state model tái sử dụng state machine của Behavior Platform. Với
speed, yaw rate và radial distance, hệ thống tạo các nhãn tính toán như
`Walk`, `Turn`, `Pause`, `Explore`, `Idle` và `Recover`; metadata có thể cung
cấp nhãn tùy chỉnh.

Report lưu state sequence, timeline, episode, duration, transition counts và
transition probabilities. Các nhãn này mô tả quy tắc phân loại trên chuỗi số
đã cung cấp, không phải phân loại sinh học. Ngưỡng là cấu hình phần mềm và
không phải ngưỡng chẩn đoán.
