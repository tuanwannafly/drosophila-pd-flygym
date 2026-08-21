# V9 Architecture

```text
ResearchKernel
    -> ResearchBus
    -> ServiceRegistry
    -> ResourceManager
    -> TaskScheduler
    -> V7 Dataset Adapter
    -> V8 Experiment Runtime
    -> existing Campaign / Study APIs
```

The kernel is additive. It does not replace V6 execution, V7 discovery, or V8
session orchestration. It stops before downstream scientific work when the
dataset adapter reports `WAITING_DATASET`.

Operational outputs are `kernel.log`, `events.json`, `timeline.json`,
`kernel_state.json`, `resources.json`, and `registry.json`.
