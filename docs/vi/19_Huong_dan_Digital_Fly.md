# 19. Hướng dẫn Digital Fly

## Tạo từ rollout

`FlyGymRolloutLoader` chuẩn hóa JSON trước. Ứng dụng truyền object rollout đó
cho `DigitalFly.fromRollout(rollout)`. Vì vậy Digital Fly không parse JSON lần
thứ hai và không thay thế `Workspace`.

```javascript
const fly = DigitalFly.fromRollout(normalizedRollout, { name: 'rollout.json' });
const report = fly.validate();
```

## Đọc trajectory

`fly.trajectories.list()` trả về các record có `name`, `flyId`, `data`, metadata
và binding component. Có thể dùng `fly.getTrajectory(name)` để truy cập một
trajectory cụ thể. Dữ liệu trả về là dữ liệu rollout đã được caller cung cấp;
không nên sửa trực tiếp record trong khi phân tích.

## Persist

`fly.toJSON()` và `DigitalFly.fromJSON(data)` phục vụ lưu trạng thái model. Đây
là persistence của metadata và dữ liệu đã nạp, không phải evidence mới.
