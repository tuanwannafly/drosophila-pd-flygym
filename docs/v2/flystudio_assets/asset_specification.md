# Asset Specification

All assets must declare an `id` string (UUID or canonical name).
- **Textures**: Must specify format (default `RGBA8`) and `mipmaps` bool.
- **Materials**: Use base PBR parameters (`albedo`, `roughness`, `metallic`). Texture references must point to valid `TextureAsset` IDs.
- **JSON Manifests**: Follow standard `{ "version": "1.0", "entries": { ... } }` layout.
