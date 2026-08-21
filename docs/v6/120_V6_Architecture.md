# V6 Architecture

```text
dataset manifest and metadata
            |
            v
  DatasetDiscovery / WAITING_DATASET gate
            |
            v
       ExecutionRuntime
            |
            v
   existing StudyOrchestrator
            |
            v
 execution report + ArtifactRegistry
```

The V6 package is additive and orchestration-only. It reuses the existing
campaign and research-pipeline APIs and does not duplicate scientific modules.
No execution path imports FlyGym or MuJoCo directly. A future ready dataset is
an external input; its provenance and payload paths must be present in its
manifest before delegation occurs.

The scientific boundary is unchanged: computational outputs are not biological
validation and no Parkinson's disease conclusion is created by this runtime.
