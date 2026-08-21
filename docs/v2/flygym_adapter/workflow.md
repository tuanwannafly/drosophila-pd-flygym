# FlyGym Adapter Workflow

1. Load and validate one YAML configuration.
2. Build a fly and world through the adapter.
3. Attach the fly through `BaseWorld.add_fly`.
4. Build `Simulation` and optionally attach its renderer.
5. Create `RolloutRecorder` and a bounded `FlyGymRuntime`.
6. Run only in an approved Python 3.12/FlyGym 2.1.0/MuJoCo 3.9.0 environment.
7. Export JSON, CSV, NPZ, metadata and manifest.

No stage creates a rollout when FlyGym is unavailable.
