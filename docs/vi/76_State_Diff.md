# 76. State Diff

State Diff Engine so sánh các field đã có trong hai `TwinState`: joint changes,
COM changes, trajectory changes, metrics delta, parameter changes và behavior
label delta.

Engine không tính metric mới. Các trường không tồn tại hoặc không so sánh được
được giữ ở dạng left/right để tránh suy diễn.
