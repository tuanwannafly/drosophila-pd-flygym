# Web Data Format

## File dich

`viewer_pose.json` co cac truong top-level:

- `metadata`: provenance va schema metadata
- `fps`: frame rate suy ra tu timestep
- `frame_count`: so frame
- `joint_names`: ten joint
- `frames`: danh sach pose theo frame

Moi frame co `frame_index`, `time`, `thorax`, `position`, `orientation`,
`COM`, `joint_angles`, `joint_velocity`, `joint_acceleration`, `contacts`,
`trajectory`, va `visibility`. Truong `joint_velocities` duoc ghi them nhu
alias tuong thich voi loader Viewer hien tai.

## Quaternion

Quaternion trong file Web dung thu tu `[x, y, z, w]`, duoc ghi ro bang
`metadata.quaternion_order = "xyzw"`. Cac quaternion `[w, x, y, z]` tu
pipeline Python duoc chuyen doi truoc khi ghi file.

## JSON Schema

Schema chinh nam tai `docs/api/viewer_pose.schema.json`. Schema mo ta cau truc
co ban; `validator.py` bo sung cac kiem tra frame index, finite values,
quaternion norm, va trajectory.

## Asset khong co

Gia tri khong co trong rollout khong duoc dien bang du lieu gia. COM, joint,
contact va visibility duoc ghi theo du lieu co that; phan thieu duoc bieu dien
bang `null`, object rong, hoac co visibility phu hop.
