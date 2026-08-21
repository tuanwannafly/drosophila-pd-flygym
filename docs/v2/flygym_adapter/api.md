# FlyGym Adapter API

Public symbols:

- `FlyGymAdapter.create_fly/create_world/attach_fly/create_simulation/create_renderer`
- `FlyBuilder.healthy/position/orientation/pose/build`
- `WorldBuilder.flat/blocks/mixed/with_fly/build`
- `SimulationBuilder.with_world/timestep/build`
- `FlyGymRuntime.run/step/reset/pause/resume/stop`
- `RolloutRecorder.record/reset`
- `export_rollout`

All APIs are typed and defer the FlyGym import until a live object is requested.
