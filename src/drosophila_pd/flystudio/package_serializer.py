import json
from .project_package import ProjectPackage

class PackageSerializer:
    @staticmethod
    def serialize_metadata(pkg: ProjectPackage) -> str:
        return json.dumps({
            "name": pkg.metadata.name,
            "author": pkg.metadata.author,
            "version": str(pkg.metadata.version),
            "description": pkg.metadata.description
        })

    @staticmethod
    def serialize_manifest(pkg: ProjectPackage) -> str:
        entries = [{"path": e.path, "checksum": e.checksum, "size": e.size_bytes} for e in pkg.manifest.entries]
        return json.dumps({"entries": entries})
