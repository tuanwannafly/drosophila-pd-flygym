# 1. Giới thiệu dự án

Fly Studio là nền tảng phần mềm để nạp, kiểm tra, phân tích, trực quan hóa
và xuất dữ liệu rollout của FlyGym. Repository gồm implementation Python cho
phân tích nghiên cứu và web platform JavaScript cho workspace, timeline,
viewer, báo cáo và các extension.

## Mục tiêu

- Giữ pipeline phân tích có thể kiểm tra và tái lập.
- Tách dữ liệu, phân tích, thống kê, trực quan hóa và export thành các lớp có
  API rõ ràng.
- Cho phép phát triển thêm tính năng mà không phá các milestone đã đóng băng.
- Cung cấp tài liệu đủ rõ để developer có thể đọc code, chạy test và tiếp tục
  mở rộng.

## Phạm vi khoa học

Các kết quả trong repository là kết quả tính toán/mô phỏng. Chúng không tự
động trở thành chẩn đoán, xác nhận bệnh Parkinson, mức độ bệnh, tương đương
dopamine hay chứng minh cơ chế sinh học.

## Nguyên tắc phát triển

Workspace là source of truth của web application. Module mới phải additive,
giữ public API hiện có và đặt reusable logic trong module riêng. Evidence,
notebook, manuscript và release artifact đã đóng băng không được sửa trong
Epic 11.
