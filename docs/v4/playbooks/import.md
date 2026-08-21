# Import Playbook

1. Identify the source file and declared rollout/schema version.
2. Validate required fields and reject malformed or incomplete input without
   changing the previous workspace.
3. Record source path, commit/configuration, environment, and checksum.
4. Normalize only through existing canonical loaders and data models.
5. Write an import manifest and a clear missing-data report.

Import must not silently repair scientific values or fabricate observations.
