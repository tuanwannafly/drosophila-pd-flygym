# Performance Report

The manager indexes normalized rollout objects rather than reparsing JSON. Dataset duplicate detection uses a stable FNV-1a fingerprint over metadata, timing, frame count, and channel edge samples. The panel limits visible experiment rows to the first 100 records to avoid unbounded DOM growth. Dashboard computation is explicit and can be called on demand; the last report is cached by `AnalyticsDashboard` until recomputed.

Large rollouts still occupy browser memory because the existing loader retains normalized channels and raw data. Streaming, chunked persistence, and worker-based analysis remain future extensions. No simulation or FlyGym execution is started by this layer.
