# Format Specification

A `.flystudio` file is a ZIP archive containing:
- `metadata.json`: Name, author, version.
- `manifest.json`: List of files and SHA256 checksums.
- `scene.json`: Scene Graph nodes.
- `viewer.json`: Viewer Layout and settings.
- `playback.json`: Temporal streams and events.
- `preview.png`: 256x256 thumbnail.
- `assets/`: Directory containing raw textures, meshes, and raw trajectory blobs.
