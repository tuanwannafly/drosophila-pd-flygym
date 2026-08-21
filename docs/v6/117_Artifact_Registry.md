# Artifact Registry

`ArtifactRegistry` records existing files by category:

`reports`, `figures`, `tables`, `validation`, `publication`, `bundle`, and
`checksums`.

Each record contains a relative path, byte size, SHA-256 digest, and optional
metadata. Registration never creates or rewrites the source artifact.
`artifact_registry.json` provides a verification summary for the execution
output directory.
