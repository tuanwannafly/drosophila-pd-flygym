# Validation khoa học và phần mềm

Validation của package hiện tập trung vào tính đúng của phần mềm và độ nhạy
của mô tả tính toán:

- bootstrap interval có seed cố định;
- leave-one-out và feature ablation;
- tương quan trên sample arrays;
- so sánh mean/median/IQR/MAD để xem độ nhạy outlier;
- kiểm tra schema, finite payload và scientific scope.

Các phép này không tự biến thành kiểm định ý nghĩa thống kê, không tạo claim
sinh học và không thay thế validation bằng dữ liệu ruồi trưởng thành ngoài
simulator. Việc đối chiếu literature phải được ghi ở lớp evidence riêng.
