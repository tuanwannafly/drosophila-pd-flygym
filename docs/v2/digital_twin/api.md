# API

## Digital Twin

```python
from drosophila_pd.behavior_platform import (
    DigitalTwin,
    TwinConfiguration,
    TwinMetadata,
    TwinState,
)

twin = DigitalTwin(
    metadata=TwinMetadata("session09_twin"),
    configuration=TwinConfiguration("config", "1.0", {"motor_scale": 1.0}),
)
twin = twin.record_state(TwinState(0.0, "Idle"))
twin = twin.record_state(TwinState(1.0, "Walk", {"speed": 12.0}))
replay = twin.replay([0.0, 0.5, 1.0])
```

## Behavioral State Machine

```python
from drosophila_pd.behavior_platform import classify_behavior_states, analyze_state_sequence

states = classify_behavior_states(speed_mm_s=speed, yaw_rate_rad_s=yaw_rate)
state_report = analyze_state_sequence(states, timestep_s=0.01)
```

## Intervention

```python
from drosophila_pd.behavior_platform import (
    InterventionDefinition,
    ParameterSchedule,
    apply_intervention_parameters,
)

intervention = InterventionDefinition(
    "computational_adjustment",
    {"coupling_scale": 0.75},
    schedules=(ParameterSchedule("motor_scale", (0.0, 10.0), (1.0, 0.8)),),
)
parameters = apply_intervention_parameters({"motor_scale": 1.0}, intervention, time_s=5.0)
```

## Laboratory and Scenarios

```python
from drosophila_pd.behavior_platform import build_experiment_catalog, build_interactive_lab

catalog = build_experiment_catalog(experiments)
lab = build_interactive_lab(catalog)
```
