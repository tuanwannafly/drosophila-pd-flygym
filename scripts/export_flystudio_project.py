import sys
import argparse
from drosophila_pd.flystudio.integration.pipeline import FlyStudioPipeline

def main():
    parser = argparse.ArgumentParser(description="Export a Fly Studio project.")
    parser.add_argument("name", help="Name of the project to export")
    parser.add_argument("output", help="Output .flystudio file path")
    args = parser.parse_args()

    print(f"Creating project '{args.name}'...")
    pkg = FlyStudioPipeline.create_project(args.name)
    print(f"Exporting to '{args.output}'...")
    FlyStudioPipeline.export_project(pkg, args.output)
    print("Export complete.")

if __name__ == "__main__":
    main()
