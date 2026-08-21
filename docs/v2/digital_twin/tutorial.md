# Tutorial

This tutorial builds a digital twin record from already computed reports.

## 1. Create a Twin

```python
twin = DigitalTwin(
    metadata=TwinMetadata("example_twin"),
    configuration=TwinConfiguration("example_config", "1.0", {"motor_scale": 1.0}),
)
```

## 2. Add States

```python
twin = twin.record_state(TwinState(0.0, "Idle"))
twin = twin.record_state(TwinState(0.5, "Walk", {"speed_mm_s": 12.0}))
```

## 3. Replay

```python
replay = twin.replay([0.0, 0.25, 0.5])
```

## 4. Add an Intervention Timeline

```python
timeline = intervention_from_config(config)
replay = replay_intervention(timeline, base_parameters={}, sample_times_s=[0.0, 1.0])
```

## 5. Export Visualizations

```python
export_advanced_visualization_set(
    state_report=state_report,
    intervention_report=intervention_report,
    similarity_report=similarity_report,
    output_dir="results/v2/session10",
)
```
