# Architecture

- **FlyStudioPipeline**: The central orchestrator that stitches everything together. It coordinates the creation of new `ProjectPackage` instances, validates them, and handles I/O via the `Exchange` format.
- **PipelineValidator**: Inspects packages for structural integrity using the Exchange Format validators.
- **PipelineReport**: Emits formatted logs for validation states (errors and warnings).
- **Scripts**: CLI entry points bridging raw datasets to `.flystudio` packages ready for the Web Viewer.
