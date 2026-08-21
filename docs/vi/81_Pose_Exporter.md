# Pose Exporter

## Muc dich

`drosophila_pd.viewer_export` la lop hau xu ly doc-only de chuyen hai artifact
rollout da co thanh mot file pose cho Three.js Viewer. Lop nay khong chay
FlyGym, khong thay doi rollout, va khong tao ket qua khoa hoc moi.

## Dau vao

Moi dataset can co:

- `rollout.json`
- `rollout_arrays.npz`

Hai file co the nam o thu muc dataset hoac trong thu muc `rollouts/`. Exporter
uu tien cac mang trong NPZ va dung JSON cho metadata, frame fields, hoac cac
truong bo sung khi co.

## Chay CLI

```text
python scripts/export_viewer_pose.py --dataset Healthy_001 --output viewer_pose.json
```

`--dataset` cung co the la duong dan den mot thu muc dataset. Co the them
`--dataset-root` nhieu lan khi dataset duoc luu ngoai cac root mac dinh.

## Quy tac du lieu

- Thorax position va orientation phai co cung so frame.
- Time phai tang deu; neu khong co time thi exporter dung `timestep_s`.
- Quaternion nguon dang `wxyz` duoc chuyen sang `xyzw` cho Viewer.
- Quaternion dau ra duoc normalize va kiem tra finite.
- Joint velocity/acceleration duoc doc tu input; chi khi khong co moi suy ra
  bang sai phan so tu joint positions da co.
- Mesh metadata chi mo ta cac thanh phan hien thi; khong them toa do mesh.

## Pham vi khoa hoc

File sinh ra la format trao doi cho truc quan tinh toan. No khong phai la
kiem dinh Parkinson, khong phai biological validation, va khong thay the
evidence frozen cua repository.
