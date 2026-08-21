# Data Flow

`raw FlyGym JSON`
`-> FlyGymRolloutLoader.parseData`
`-> normalized rollout and validation`
`-> AnalysisPipeline`
`-> feature/statistics/QC/outlier outputs`
`-> StatisticalEngine and comparison`
`-> Parkinson analytics`
`-> SVG/JSON/CSV/Markdown/HTML`
`-> WorkspacePersistence`

Each stage consumes the previous stage output. No synthetic scientific result is introduced by the integration adapter.
