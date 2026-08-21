# Scheduler

Scheduler phân loại experiment theo dependency, priority và batch. Các trạng
thái gồm `QUEUED`, `READY`, `RUNNING`, `PAUSED`, `CANCELLED`, `COMPLETED`,
`FAILED` và `RETRY`. Scheduler không có vòng lặp simulation riêng.
