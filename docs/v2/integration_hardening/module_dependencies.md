# Module Dependency Diagram

```text
IntegrationWorkflow
  |-- FlyGymRolloutLoader
  |-- computeRolloutStatistics
  |-- AnalysisPipeline
  |     |-- ParkinsonAnalyticsEngine
  |     |-- quality/normalization/cache/matrix
  |-- StatisticalEngine
  |-- ExperimentWorkspace
  |-- renderAnalyticsSVG / AnalyticsExporter
  |-- WorkspacePersistence
```

The diagram describes software dependencies only. It does not add scientific provenance to frozen evidence.
