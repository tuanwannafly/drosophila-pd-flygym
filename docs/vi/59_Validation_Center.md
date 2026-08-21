# 59. Validation Center

Validation Center chỉ đọc và tóm tắt validation report đã có. Các trường có
thể hiển thị gồm RMSE, MAE, R2, correlation, bootstrap, cross-validation,
effect size, outliers, missing values và warnings khi report cung cấp chúng.

Nếu chưa attach report, trạng thái là `NOT_AVAILABLE`. Module không tự chạy
simulation, không thêm thuật toán thống kê và không nâng cấp kết luận thành
biological validation.
