# Epic 16 — Mô hình Parkinson tính toán

Epic 16 bổ sung lớp phân tích hậu xử lý cho Digital Fly và rollout thật. Lớp
này bao phủ trích xuất đặc trưng vận động, mô hình trạng thái hành vi, chỉ số
tính toán có trọng số, validation độ nhạy, so sánh và report/export.

## Ranh giới khoa học

Đây là computational/phenomenological analysis only. Không có chẩn đoán y khoa,
Parkinson disease validation, disease severity mapping, dopamine equivalence,
mechanistic equivalence hoặc biological treatment claim. Không có simulation
logic mới và không có perturbation mới.

## API chính

- `ParkinsonMotorModel`: đo một `RolloutData`.
- `ComputationalPDIndex`: tính độ lệch có reference, weight và direction.
- `compare_computational_reports`: so sánh nhiều điều kiện tính toán.
- `generate_computational_pd_report`: ghi JSON, CSV, Markdown, HTML và hình.
- `scripts/analyze_computational_pd.py`: CLI cho rollout JSON đã xuất.

## Kiểm thử

Fixture trong test là dữ liệu số cố định cho contract phần mềm, không phải bằng
chứng khoa học. Kết quả khoa học mới chỉ có thể thu được khi chạy lớp này trên
rollout thật đã tồn tại và giữ nguyên provenance.
