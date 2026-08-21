import io
import zipfile
import json
from .project_package import ProjectPackage
from .metadata import ProjectMetadata
from .versioning import Version

class PackageLoader:
    @staticmethod
    def load(data: bytes) -> ProjectPackage:
        buf = io.BytesIO(data)
        with zipfile.ZipFile(buf, 'r') as zf:
            meta_dict = json.loads(zf.read("metadata.json").decode('utf-8'))
            metadata = ProjectMetadata(
                name=meta_dict.get("name", ""),
                author=meta_dict.get("author", "Unknown"),
                version=Version.from_string(meta_dict.get("version", "1.0.0")),
                description=meta_dict.get("description", "")
            )

            pkg = ProjectPackage(metadata=metadata)

            if "scene.json" in zf.namelist():
                pkg.scene_data = json.loads(zf.read("scene.json").decode('utf-8'))
            if "viewer.json" in zf.namelist():
                pkg.viewer_data = json.loads(zf.read("viewer.json").decode('utf-8'))
            if "playback.json" in zf.namelist():
                pkg.playback_data = json.loads(zf.read("playback.json").decode('utf-8'))

            if "preview.png" in zf.namelist():
                pkg.preview_image = zf.read("preview.png")

        return pkg
