# Prediction Hook

`predict_next_frame()` và `estimate_state()` chỉ là interface hook. Mặc định
hai hàm trả về `null`; runtime không chứa AI, model dự báo, huấn luyện hay
tham số sinh học.

Ứng dụng tương lai có thể truyền callback qua `predictionHooks` và tự chịu
trách nhiệm về provenance, validation và giới hạn diễn giải. Prediction buffer
được tách khỏi frame stream thật và không được xem là dữ liệu quan sát.
