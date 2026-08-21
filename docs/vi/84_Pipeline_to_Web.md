# Pipeline den Web Viewer

## Luong du lieu

```text
FlyGym rollout da import
        |
        +-- rollout.json
        +-- rollout_arrays.npz
        |
        v
viewer_export (read-only)
        |
        v
viewer_pose.json
        |
        v
web/viewer/pose_loader.js
        |
        v
Three.js Digital Fly Viewer
```

Exporter la bien gioi giua Python pipeline va Web Viewer. Viewer khong doc
NPZ va exporter khong biet chi tiet renderer; hai ben giao tiep qua
`viewer_pose.json`.

## Reproducibility

Metadata ghi dataset id, file nguon, schema version, timestep va quaternion
order. Cung mot input va cung mot output path se tao JSON on dinh, voi key
duoc sap xep va JSON UTF-8.

## Gioi han

Pipeline nay khong chay simulation, khong sua controller, khong cap nhat
evidence frozen, va khong ket luan ve sinh hoc hay benh Parkinson. Neu rollout
khong co mot observable, output khong tuong ung se de trong/`null` va
visibility phan anh viec do.

## Kiem thu thu cong

1. Chuan bi rollout that theo dataset contract.
2. Chay CLI exporter.
3. Kiem tra `validation.overall_pass` va `frame_count`.
4. Mo `viewer_pose.json` bang Viewer hien co.
5. Kiem tra frame dau/cuoi va orientation trong console trinh duyet.
