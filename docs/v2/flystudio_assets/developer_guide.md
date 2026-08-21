# Developer Guide

When extending the Asset Pipeline:
- **No Physics/Rendering Code**: Do not parse OBJ/GLTF files directly in these classes, and do not make OpenGL calls. This module strictly handles *metadata* and *routing*.
- **Memory Management**: Use `size_mb` when inserting into the `AssetCache` to ensure the LRU eviction policy works correctly.
- **Serialization**: Ensure all new Asset types can be dumped into `AssetManifest` dictionaries via standard `dataclasses.asdict()`.
