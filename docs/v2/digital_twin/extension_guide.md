# Extension Guide

## New State Labels

Add user-defined labels through `custom_labels` in
`classify_behavior_states()` or by supplying explicit label sequences to
`analyze_state_sequence()`.

## New Intervention Types

Represent new virtual interventions as `InterventionDefinition` records with
parameter modifications and schedules. Do not encode biological treatment
claims in intervention names or metadata.

## New Scenario Types

Use `build_scenario()` for new roles. Scenarios should remain data records
unless an authorized execution layer is added separately.

## New Visualizations

Add deterministic exporters to `advanced_visualization.py` and include PNG,
SVG, PDF, and HTML support when practical.
