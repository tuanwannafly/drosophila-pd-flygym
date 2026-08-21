# Pipeline

The v2 behavioral platform is a post-processing pipeline.

```text
existing rollout arrays
        |
        v
RolloutData validation
        |
        v
behavioral measurement engine
        |
        +--> trajectory, speed, heading, yaw, yaw rate
        +--> walking, pause, freezing, duty cycle
        +--> turning, cumulative turning, left/right bias
        +--> curvature, tortuosity, exploration
        +--> COM, joint, adhesion summaries
        |
        v
exports: CSV, JSON, NPZ, PNG
        |
        v
viewer plans and offline rendering
        |
        v
Healthy/Candidate/Rescue comparison reports
```

## Runtime Separation

Numerical measurement and export are CPU-only. Interactive MuJoCo viewing
requires an interactive runtime with MuJoCo available, but the repository
stores viewer plans rather than requiring viewer execution during tests.

Offline rendering can create PNG sequences directly. GIF and MP4 encoding are
backend-dependent and fall back to PNG frames when an encoder is unavailable.
