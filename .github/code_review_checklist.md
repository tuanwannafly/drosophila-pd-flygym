# Code Review Checklist

- [ ] Scope is small and matches the issue or task.
- [ ] Existing APIs and package patterns were inspected.
- [ ] No frozen evidence, manuscript, notebook, or release artifact changed
  unintentionally.
- [ ] Tests cover changed behavior.
- [ ] No new dependency is unnecessary.
- [ ] Errors and provenance are explicit.
- [ ] `compileall`, `pytest`, and `git diff --check` pass.
- [ ] Scientific language is separated from software behavior.
