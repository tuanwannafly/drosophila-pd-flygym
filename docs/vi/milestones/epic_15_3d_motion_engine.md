# Epic 15 — Digital Fly 3D Motion Engine

## Kiến trúc

```text
FlyGymRolloutLoader
        ↓
    DigitalFly
        ↓
    DigitalFly3D
   ├── Skeleton3D / Bone3D / Joint3D
   ├── FK + pose interpolation
   ├── trajectory sampling
   └── computational metrics / validation
        ↓
 Canvas DigitalFly3DRenderer
```

## Ranh giới

Epic 15 chỉ thêm lớp dữ liệu, motion hậu xử lý, Canvas projection và validation.
Không sửa FlyGym, simulation, controller, frozen evidence hay manuscript. Không
gán ý nghĩa Parkinson cho state hoặc metric.

## Validation

Contract tests kiểm tra hierarchy, FK API, interpolation, renderer integration,
documentation và không thêm simulation module mới. Full pytest vẫn giữ các
integration skip dành cho Colab khi FlyGym/MuJoCo không có trong môi trường.
