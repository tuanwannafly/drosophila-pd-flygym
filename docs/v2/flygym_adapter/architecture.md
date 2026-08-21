# FlyGym Adapter Architecture

```text
FlyGymConfig
    |
FlyGymAdapter / Builders
    |
FlyGym 2.1.0 objects
    |
FlyGymRuntime -> RolloutRecorder -> Exporter
```

`factory.py` là module duy nhất lazy-import các API FlyGym. `runtime.py` không
biết cách xây fly/world; `recorder.py` chỉ gọi observation getters; `export.py`
không gọi simulation.

The adapter does not call `add_joints()` and does not assign `fly.skeleton`.
Those operations remain under the existing authorized materialization boundary.
