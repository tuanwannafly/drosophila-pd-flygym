# Session09 Mapping

Session09 is the digital twin and behavioral replay session.

Expected Session09 work:

- create `DigitalTwin` records from rollout-derived metrics
- store `TwinState`, `TwinHistory`, `TwinSnapshot`, and `TwinReplay` records
- reconstruct timelines deterministically
- classify behavioral states and extract behavioral episodes
- export state timelines and behavioral network diagrams

Session09 should not execute simulations or modify frozen v1 artifacts.
