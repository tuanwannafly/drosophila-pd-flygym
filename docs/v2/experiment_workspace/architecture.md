# Experiment Workspace Architecture

The Experiment Workspace is an additive browser-side management layer above the existing scene and FlyGym rollout loaders. It does not run simulations and does not change frozen evidence.

## Components

- `ExperimentManager` stores named computational experiment records, kinds, folders, tags, notes, and rollout references.
- `DatasetManager` indexes normalized rollouts, fingerprints them, detects duplicates, checks required frame data, and reports compatible channels.
- `ComparisonWorkspace` stores selected experiment IDs, alignment, synchronization, and comparison frame.
- `ExperimentComparisonModel` adapts selected rollouts to the existing comparison implementation.
- `AnalyticsDashboard` computes finite computational summaries, distributions, histograms, box-plot statistics, scatter rows, and trends.
- `ExperimentReportGenerator` exports JSON, Markdown, HTML, CSV, or browser print output for PDF creation.
- `SnapshotStore`, `LayoutManager`, and `PluginRegistry` provide workspace snapshots, panel layout state, and typed extension points.

`Workspace` remains the source of truth for the loaded scene, current frame, selection, and playback. The experiment workspace is a separate registry for multiple loaded rollouts. No component makes a biological interpretation from the labels `Healthy`, `PD`, `Candidate`, or `Control`; these are computational organization labels only.
