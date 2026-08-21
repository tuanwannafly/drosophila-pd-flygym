# 64. Experiment Queue

`ExperimentQueueManager` là lớp persistence cho các job experiment hiện có.
Nó sử dụng `ExperimentRunner` và `ExperimentScheduler` với stage handlers do
caller cung cấp.

Các trạng thái gồm queued/pending, running, retrying, completed, failed và
cancelled. Checkpoint, progress, ETA, duration và log chỉ mô tả điều phối;
queue không tự chạy simulation.
