# Tái lập kết quả

`hash_payload` tạo SHA-256 ổn định cho output JSON-compatible. Những hàm
`repeated_execution_check` và `seed_consistency_check` chạy lại operation hậu
xử lý được truyền vào và so sánh hash.

Đây là reproducibility của software output. Muốn tái lập một kết quả nghiên cứu,
cần lưu cùng rollout nguồn, metadata, seed, cấu hình, commit và manifest hash.
Framework không tự khẳng định một rollout chưa được cung cấp.
