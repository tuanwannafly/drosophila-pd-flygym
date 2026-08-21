# Tiếp tục campaign

Queue được lưu tại `results/progress/jobs.json`. Khi chạy lại lệnh batch,
job `COMPLETED` được giữ nguyên và không được chạy lại. Dùng `--no-resume`
chỉ khi cần bỏ qua trạng thái đã lưu cho một lần chuẩn bị lại.
