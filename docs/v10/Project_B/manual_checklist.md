# Manual Checklist

- [ ] Confirm no rollout or synthetic data exists in the Project B package.
- [ ] Confirm the matrix contains exactly `PD_001` through `PD_100`.
- [ ] Confirm seeds are 0 through 99 and all rows are `PLANNED`.
- [ ] Confirm no approved PD configuration is falsely claimed.
- [ ] Confirm manifest and metadata templates are planning-only.
- [ ] Confirm required directory tree and expected outputs are documented.
- [ ] Confirm absent data stops the existing CLI/runtime at `WAITING_DATASET`.
- [ ] Confirm no scientific, biological, or frozen-evidence claim changed.
- [ ] Run compileall, pytest, Markdown validation, schema validation, and
      `git diff --check`.
