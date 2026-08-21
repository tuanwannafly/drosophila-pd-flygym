# Integration Workflow

```text
datasets/<type>/<version>/manifest.json
                    |
                    v
          FlyGym Dataset Adapter
                    |
                    v
             DatasetValidator
                    |
                    v
        V6 ExecutionRuntime gate
                    |
                    v
          existing StudyOrchestrator
```

The adapter validates the external dataset before execution. The downstream
analysis, statistics, computational-PD, validation, and publication modules
remain the existing APIs; V7 does not duplicate them.
