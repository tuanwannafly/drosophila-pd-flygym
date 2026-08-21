# Epic 14 — Digital Fly Model

## Mục tiêu

Epic 14 bổ sung một data model cho thực thể Digital Fly. Model kết nối body,
skeleton, joints, các component hình thái, pose/motion và trajectory registry
trong một object có `flyId` ổn định trong vòng đời của model.

## Tích hợp

Rollout đi qua `FlyGymRolloutLoader` như trước. Sau khi loader chuẩn hóa thành
công, `App` gọi `DigitalFly.fromRollout()` và đăng ký object trong
`DigitalLaboratory`. Workspace, loader, FlyGym và simulation pipeline không bị
thay thế.

## Ranh giới khoa học

Epic này không chạy simulation, không gọi FlyGym, không tạo trajectory giả và
không thêm kết luận Parkinson. `ParkinsonStateModel` chỉ lưu computational
metadata; mọi diễn giải sinh học vẫn bị loại khỏi model.

## Kiểm thử

Contract tests kiểm tra public model, rollout integration, ownership field và
tài liệu. Full repository tests vẫn là kiểm tra hồi quy chính; các integration
test cần FlyGym/MuJoCo tiếp tục được skip khi môi trường không có dependency.
