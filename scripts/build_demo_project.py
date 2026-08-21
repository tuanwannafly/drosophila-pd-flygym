import sys
from drosophila_pd.flystudio.integration.pipeline_examples import PipelineExamples

def main():
    print("Building healthy.flystudio...")
    h = PipelineExamples.build_healthy()
    print(f"Generated {h}")

    print("Building candidate.flystudio...")
    c = PipelineExamples.build_candidate()
    print(f"Generated {c}")

    print("Building comparison.flystudio...")
    comp = PipelineExamples.build_comparison()
    print(f"Generated {comp}")

    print("All demo projects built successfully.")

if __name__ == "__main__":
    main()
