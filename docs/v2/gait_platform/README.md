# V2 Locomotion Gait Platform

This directory documents the canonical gait-analysis platform for Sessions
05-06. The subsystem extends v2 rollout post-processing with gait, contact,
coordination, visualization, animation, and export tooling.

## Documents

- [Architecture](architecture.md)
- [API](api.md)
- [Tutorial](tutorial.md)
- [Developer Guide](developer_guide.md)
- [Scientific Interpretation](scientific_interpretation.md)
- [Session Mapping](session_mapping.md)

## Boundary

The gait platform operates on existing rollout arrays. It does not run
simulations, modify controllers, introduce perturbations, or change frozen v1
evidence and manuscript artifacts.
