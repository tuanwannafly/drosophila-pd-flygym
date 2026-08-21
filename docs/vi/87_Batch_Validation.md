# Batch Validation

Batch validation chỉ đọc các result JSON hiện có và gom những trường validation
đã được ghi như `overall_pass`, RMSE, MAE, correlation, effect size, warnings,
outliers và missing data. Module không tự tạo metric mới.
