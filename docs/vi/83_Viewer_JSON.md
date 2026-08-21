# Viewer JSON

## Vi du toi thieu

```json
{
  "metadata": {"schema_version": "viewer-pose-1.0", "quaternion_order": "xyzw"},
  "fps": 60.0,
  "frame_count": 1,
  "joint_names": [],
  "frames": [
    {
      "frame_index": 0,
      "time": 0.0,
      "thorax": [0.0, 0.0, 0.0],
      "position": [0.0, 0.0, 0.0],
      "orientation": [0.0, 0.0, 0.0, 1.0],
      "COM": null,
      "joint_angles": {},
      "joint_velocity": {},
      "joint_acceleration": {},
      "contacts": {},
      "trajectory": {"thorax": [0.0, 0.0, 0.0]},
      "visibility": {"mesh": true, "skeleton": false, "COM": false, "trajectory": true}
    }
  ]
}
```

Day la vi du cau truc, khong phai rollout khoa hoc va khong duoc dung lam
evidence. File hop le phai duoc sinh tu rollout da import va pass ca JSON
Schema lan validator runtime.

## Kiem tra

```text
python scripts/export_viewer_pose.py --dataset path/to/Healthy_001 --output viewer_pose.json
```

CLI chi ghi file output. Neu input loi, exporter dung voi thong bao loi thay
vi ghi mot file khong hop le.
