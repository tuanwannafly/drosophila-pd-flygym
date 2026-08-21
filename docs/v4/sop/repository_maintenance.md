# SOP: Repository Maintenance

1. Keep changes scoped and inspect protected paths before editing.
2. Prefer additive docs/tests and preserve public APIs.
3. Keep raw/generated outputs ignored unless explicitly curated.
4. Run compileall, pytest, Markdown validation, CLI/package smoke checks, and
   `git diff --check`.
5. Review the final diff, commit intentionally, and verify the remote state.
