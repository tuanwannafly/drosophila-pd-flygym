# V8 Architecture

```text
V7 Dataset Adapter
        |
        v
Experiment Session + Events
        |
        v
Existing Campaign / StudyOrchestrator
        |
        v
Runtime persistence + Research Package reference
```

V8 is additive orchestration. It does not duplicate or modify the dataset
adapter, campaign engine, analysis, statistics, computational-PD, validation,
Digital Twin, or publication implementations.

The scientific boundary remains unchanged: runtime completion is software
workflow status, not biological validation or a Parkinson's disease claim.
