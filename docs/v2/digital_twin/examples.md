# Examples

## Scenario Comparison

```python
healthy = build_scenario("healthy", role="Healthy", parameters={"motor_scale": 1.0})
candidate = build_scenario("candidate", role="Candidate", parameters={"motor_scale": 0.8})
results = batch_execute_scenarios([healthy, candidate], executor)
report = compare_scenarios(results)
```

The `executor` is supplied by the caller. The scenario layer does not run
simulations by itself.

## Laboratory Layout

```python
layout = LabLayout(
    "compact",
    panels=("experiment_browser", "metric_explorer", "synchronized_replay"),
    selected_conditions=("Healthy", "Candidate"),
)
save_lab_layout(layout, "results/v2/layouts/compact.json")
```
