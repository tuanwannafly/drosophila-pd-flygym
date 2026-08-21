# Mô hình Parkinson tính toán

Package `drosophila_pd.parkinson` là lớp hậu xử lý cho rollout đã được nhập.
Nó trích xuất các đặc trưng vận động, trạng thái hành vi và các chỉ số có trọng
số do người dùng cấu hình. Package không chạy FlyGym/MuJoCo và không thay đổi
rollout.

## Phạm vi

Đây là mô hình tính toán của các đầu ra vận động. Từ “Parkinson” trong tên API
chỉ là nhãn kỹ thuật của package; không phải chẩn đoán, xác nhận sinh học,
ánh xạ mức độ bệnh, tương đương dopamine hay tương đương cơ chế.

## Luồng dữ liệu

`RolloutData` → `measure_rollout_behavior` → `extract_motor_features` →
`build_behavior_model` → `ComputationalPDIndex` → report/export.

CLI tương ứng là `scripts/analyze_computational_pd.py`. Báo cáo cần một
reference feature set nếu muốn tính chỉ số so sánh; nếu thiếu reference, các
đặc trưng vẫn được xuất nhưng chỉ số được đánh dấu chưa khả dụng.
