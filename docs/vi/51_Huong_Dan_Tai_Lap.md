# Huong dan tai lap Sprint 1

1. Checkout dung git commit va cai dependency cua repository.
2. Chuan bi cac handler pipeline that trong moi truong FlyGym phu hop.
3. Chay CLI voi mot handler cho moi stage canonical.
4. Kiem tra `manifest.json`, `job.json`, log JSONL va SHA-256.
5. Khi gian doan, chay lai voi `--resume`; scheduler se giu retry co gioi
   han va bo qua experiment da hoan thanh.

Neu FlyGym khong co trong runtime, chi co the kiem tra orchestration va
metadata. Khong dung synthetic dataset de thay the rollout that.
