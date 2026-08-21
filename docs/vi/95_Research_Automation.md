# Tự động hóa nghiên cứu

Lớp `research_execution` mở rộng runtime hiện có bằng kế hoạch campaign,
queue tuần tự, trạng thái job và các file tiến độ. Lớp này chỉ điều phối dữ liệu
rollout đã có, không chạy FlyGym và không tạo dữ liệu mới.

Campaign được đọc từ `research/campaigns/*/campaign.yaml` và
`experiment_matrix.csv`. Vì vậy số lượng experiment, seed và tên dataset không
được hardcode trong runtime.
