# Kernel CLI

The CLI is `scripts/kernel.py`.

Commands:

- `boot`: initialize the kernel and execute the orchestration graph.
- `status`: report persisted kernel state.
- `resources`: report tracked datasets and operational artifacts.
- `events`: print the persisted research bus history.
- `shutdown`: persist a clean shutdown state.

Use `--output` to select an operational output directory. The default is under
`results/kernel/default/`.
