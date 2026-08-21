# V9 Scientific Operating System

V9 adds an orchestration-only Research Kernel over the existing V7 dataset
adapter, V8 experiment runtime, campaign API, and study API.

The kernel does not implement simulation, analysis, statistics, validation,
Digital Twin behavior, or scientific interpretation. With no approved dataset
in this repository, `boot` stops at `WAITING_DATASET`.

```bash
python scripts/kernel.py boot
python scripts/kernel.py status
python scripts/kernel.py resources
python scripts/kernel.py events
python scripts/kernel.py shutdown
```

See [V9 Architecture](138_V9_Architecture.md) for the integration boundary.
