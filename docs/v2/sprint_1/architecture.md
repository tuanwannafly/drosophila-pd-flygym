# Sprint 1 architecture

The production layer is additive and handler-driven:

`ExperimentJob -> ExperimentRunner -> ordered stage handlers -> ArtifactLayout`

`ExperimentQueue -> ExperimentScheduler -> retry/resume/progress`

`DatasetManager -> manifest/checksum/verification`

`ArtifactManager -> deterministic experiment directories`

`PublicationAssetManager -> existing figure/table registration`

No class in this layer imports FlyGym or MuJoCo. The owner of the execution
environment supplies real handlers and real input files.
