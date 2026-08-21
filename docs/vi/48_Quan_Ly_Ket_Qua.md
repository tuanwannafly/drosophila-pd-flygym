# Quan ly ket qua

Moi experiment co mot thu muc theo `job_id` va cac nhom artifact:

```text
rollout/ digital_fly/ analysis/ statistics/ validation/
figures/ reports/ logs/ publication/ manifest.json
```

`manifest.json` ghi trang thai, so lan thu, configuration hash, git commit,
stage summaries va hash cua cac file. `logs/experiment.jsonl` ghi event co
cau truc. Khi stage that bai, runner ghi loi va ket thuc o trang thai FAILED;
khong xoa hay ghi de du lieu nguon.

`ExperimentScheduler` ho tro FIFO, retry co gioi han, bo qua job COMPLETED va
resume tu trang thai da luu.
