import sys
import argparse
from drosophila_pd.flystudio.integration.pipeline import FlyStudioPipeline

def main():
    parser = argparse.ArgumentParser(description="Import and validate a Fly Studio project.")
    parser.add_argument("input", help="Input .flystudio file path")
    args = parser.parse_args()

    print(f"Loading '{args.input}'...")
    pkg = FlyStudioPipeline.import_project(args.input)
    print(f"Loaded project: {pkg.metadata.name} v{pkg.metadata.version}")

    report = FlyStudioPipeline.verify_integrity(pkg)
    if report.is_valid:
        print("Project is valid.")
    else:
        print("Project validation failed:")
        for err in report.errors:
            print(f" - ERROR: {err}")

    for warn in report.warnings:
        print(f" - WARNING: {warn}")

if __name__ == "__main__":
    main()
