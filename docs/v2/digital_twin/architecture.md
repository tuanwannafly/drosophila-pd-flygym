# Architecture

The digital twin platform is a pure computational record, replay, scenario, and
visualization layer. It does not run FlyGym or MuJoCo and does not modify v1
evidence, manuscripts, notebooks, publication packages, archive packages, or
release artifacts.

## Modules

- `digital_twin.py`: `DigitalTwin`, `TwinState`, `TwinMetadata`,
  `TwinHistory`, `TwinConfiguration`, `TwinSnapshot`, `TwinReplay`, and
  `TwinScenario`.
- `state_machine.py`: behavioral state classification, transition graphs,
  transition probabilities, durations, episodes, and timelines.
- `intervention.py`: generic computational parameter interventions, staged
  schedules, deterministic replay, and before/after comparison.
- `lab.py`: experiment browser/catalog abstractions, rollout explorer layout,
  synchronized replay layout, metric explorer, and layout persistence.
- `advanced_visualization.py`: state timelines, intervention timelines, radar
  plots, Sankey-style transition diagrams, network graphs, trajectory clusters,
  progression maps, similarity heatmaps, embeddings, and replay dashboards.
- `scenario.py`: Healthy, Candidate, Progression, Future Intervention, and
  custom scenario records, batch execution hooks, and comparison reports.

## Data Flow

```text
rollout-derived reports
  -> behavioral state machine
  -> digital twin history
  -> scenario/intervention replay
  -> comparison reports
  -> visualization/lab exports
```
