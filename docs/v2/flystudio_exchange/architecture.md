# Architecture

- **ProjectPackage**: The core in-memory representation of a session. It contains metadata, scene graph data, viewer layouts, playback temporal states, and bundled assets.
- **Manifest**: Tracks checksums of all internal files for validation and tampering detection.
- **PackageBuilder**: Compresses `ProjectPackage` into a ZIP archive `.flystudio` format.
- **PackageLoader**: Reads a ZIP archive into a `ProjectPackage`.
- **Validation & Migration**: Ensures forward and backward compatibility using strict versioning definitions.
