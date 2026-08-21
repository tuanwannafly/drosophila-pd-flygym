# 20. Mô hình dữ liệu Fly

```text
DigitalFly
├── BodyModel
│   └── BodySegments
├── SkeletonModel
│   └── Bones
├── JointModel
├── WingModel
├── LegModel
├── HeadModel
├── COMModel
├── OrientationModel
├── PoseModel
├── MotionModel
├── ParkinsonStateModel
└── TrajectoryRegistry (flyId)
```

Các hierarchy giữ tên, id, parent và metadata. Các component giữ danh sách
trajectory reference; dữ liệu trajectory thực tế thuộc `TrajectoryRegistry` của
Digital Fly. Thiết kế này cho phép thêm component mà không cần đổi loader.
