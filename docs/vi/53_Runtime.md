# FlyGym Runtime

`FlyGymRuntime` là state machine đồng bộ gồm `Stopped`, `Paused` và `Running`.
`run(steps=...)` thực hiện số bước được chỉ định; không dùng timer,
`requestAnimationFrame`, playback loop hay scheduler nền.

API chính:

- `run()` chạy một khoảng bước hữu hạn hoặc `max_steps` đã cấu hình.
- `step()` tiến đúng một bước.
- `reset()` gọi reset của Simulation và recorder.
- `pause()`, `resume()`, `stop()` điều khiển state.
- `is_running`, `current_time`, `current_step` đọc trạng thái hiện tại.

Runtime không quyết định controller, perturbation hoặc diễn giải sinh học.
