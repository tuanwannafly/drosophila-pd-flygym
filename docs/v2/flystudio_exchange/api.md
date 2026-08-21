# API Reference

- `Version`: Semantic versioning container.
- `ProjectMetadata`: Global string tags.
- `ProjectPackage`: The unified data object.
- `Manifest` & `ManifestEntry`: Package internal directory listing.
- `PackageBuilder.build(pkg)`: Returns ZIP bytes.
- `PackageLoader.load(bytes)`: Returns `ProjectPackage`.
- `PackageValidator.validate(pkg)`: Returns list of structural errors.
- `ThumbnailGenerator` / `PreviewGenerator`: Utilities for the `preview.png`.
- `PackageSerializer`: Internal JSON serialization logic.
- `Migration`: Upgrade paths.
