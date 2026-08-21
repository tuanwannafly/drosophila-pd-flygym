import io
import zipfile
import json
from .project_package import ProjectPackage
from .package_serializer import PackageSerializer
from .preview_generator import PreviewGenerator

class PackageBuilder:
    @staticmethod
    def build(pkg: ProjectPackage) -> bytes:
        PreviewGenerator.generate(pkg)

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            metadata_str = PackageSerializer.serialize_metadata(pkg)
            zf.writestr("metadata.json", metadata_str)
            pkg.manifest.add_entry("metadata.json", metadata_str.encode('utf-8'))

            scene_str = json.dumps(pkg.scene_data)
            zf.writestr("scene.json", scene_str)
            pkg.manifest.add_entry("scene.json", scene_str.encode('utf-8'))

            viewer_str = json.dumps(pkg.viewer_data)
            zf.writestr("viewer.json", viewer_str)
            pkg.manifest.add_entry("viewer.json", viewer_str.encode('utf-8'))

            playback_str = json.dumps(pkg.playback_data)
            zf.writestr("playback.json", playback_str)
            pkg.manifest.add_entry("playback.json", playback_str.encode('utf-8'))

            if pkg.preview_image:
                zf.writestr("preview.png", pkg.preview_image)
                pkg.manifest.add_entry("preview.png", pkg.preview_image)

            for name, data in pkg.assets.items():
                asset_path = f"assets/{name}"
                zf.writestr(asset_path, data)
                pkg.manifest.add_entry(asset_path, data)

            manifest_str = PackageSerializer.serialize_manifest(pkg)
            zf.writestr("manifest.json", manifest_str)

        return buf.getvalue()
