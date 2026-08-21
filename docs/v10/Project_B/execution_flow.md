# Execution Flow

```text
Approved dataset supplied
  -> V7 discovery and integrity validation
  -> READY gate
  -> V6/V8/V9 orchestration
  -> existing measurements and analysis
  -> existing validation and reports
  -> publication review and archive
```

If the dataset is absent or invalid, the flow stops at `WAITING_DATASET`.
Project B does not run FlyGym, repair data, or fabricate a report.
