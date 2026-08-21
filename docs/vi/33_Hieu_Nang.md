# Hiệu năng

Pipeline validation có benchmark opt-in cho import đã chuẩn hóa, feature
extraction, analysis, statistics, visualization và export thông qua callable
do caller cung cấp. Kết quả gồm thời gian trung bình/min/max và peak memory.

Không có simulation tự động trong benchmark. Scalability phải được đánh giá
trên các kích thước dữ liệu thật được đăng ký; không dùng rollout giả để tạo
biểu đồ hiệu năng.
