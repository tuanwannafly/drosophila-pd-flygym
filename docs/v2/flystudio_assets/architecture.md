# Architecture

- **Asset Database**: The central registry (`AssetDatabase`) manages UUID mapping, tagging, and versioning.
- **Resource Manager & Cache**: `ResourceManager` coordinates with `AssetLoader` and `AssetCache` (LRU) to lazily load and manage memory limits for large assets.
- **Asset Types**:
  - `MeshAsset`: Vertices, normals, UV counts.
  - `TextureAsset`: Dimensions, format, mipmaps.
  - `MaterialAsset`: Renderer-agnostic PBR fields (albedo, roughness, metallic).
  - `AnimationAsset`: Timelines, events, and clips.
  - `TrajectoryAsset`: Spatial replay frames and metadata.
- **Validation**: `AssetValidator` checks dependencies, missing files, and duplicate IDs.
- **Manifests & Bundles**: `AssetManifest` for JSON-serializable catalogs, `AssetBundle` for grouping.
