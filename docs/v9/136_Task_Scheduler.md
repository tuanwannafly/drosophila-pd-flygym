# Task Scheduler

`TaskScheduler` runs explicit dependency graphs. The V9 graph is:

```text
prepare -> bind -> run -> validate -> package -> archive
```

If an upstream task returns `WAITING_DATASET`, downstream tasks are not run or
reported as completed. This preserves the V7/V8 dataset gate.
