# Dataset Rollout

Một rollout được xuất trong thư mục riêng:

```text
Healthy_001/
  manifest.json
  rollout.json
  rollout.csv
  rollout.npz
  metadata.json
```

`manifest.json` ghi schema version, số frame, kích thước byte, SHA-256 và
phạm vi khoa học. JSON là bản đầy đủ; CSV thuận tiện kiểm tra; NPZ giữ các
mảng số khi mọi frame có cùng shape.

Adapter không tự phát hiện hoặc ghi đè dataset đã có. Việc đặt tên, checksum
và phê duyệt dataset vẫn thuộc Dataset Registry/Adapter hiện hành.
