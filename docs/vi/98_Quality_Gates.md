# Quality gates

Một job chỉ được đánh dấu có thể publication khi cả bốn điều kiện đều đạt:

- manifest dataset hợp lệ;
- `viewer_pose.json` được export và validation thành công;
- output phân tích tồn tại;
- validation report báo pass và có dữ liệu validation.

Nếu một điều kiện không đạt, job vẫn ghi lại lỗi và artifact đã có nhưng
publication bị chặn. Đây là trạng thái kỹ thuật, không phải kết luận sinh học.
