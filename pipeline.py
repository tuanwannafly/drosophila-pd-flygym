"""
Unified Execution Pipeline for Drosophila Neural Circuit & Electrophysiology Testing.
Runs simulations (via PyTorch backend), performs neuron-level and nervous-system metric evaluation,
exports data, and opens the visualizer.
"""

import sys
import os
import argparse
from pathlib import Path
import subprocess

# Ensure code and current dir are in python path
ROOT_DIR = Path(__file__).resolve().parent
CODE_DIR = ROOT_DIR / "code"
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(CODE_DIR))

from benchmark import get_experiment, EXPERIMENTS, BenchmarkLogger
from data_processing import load_spike_data, load_annotations, compute_neuron_metrics, compute_population_metrics
from evaluate_dataset import generate_evaluation_report


def run_simulation(experiment_name: str = "sugar", t_run: float = 1.0, n_run: int = 1) -> Path:
    """
    Executes whole-brain PyTorch spiking simulation and outputs spikes to data/results.
    """
    print("=" * 70)
    print(f"STEP 1: Executing Neural Simulation (Exp: {experiment_name}, Duration: {t_run}s, Trials: {n_run})")
    print("=" * 70)

    import torch
    from run_pytorch import run_all_benchmarks

    logger = BenchmarkLogger(log_file=None)
    exp = get_experiment(experiment_name)

    results = run_all_benchmarks(
        t_run_values=[t_run],
        n_run_values=[n_run],
        experiment=exp,
        logger=logger
    )

    expected_output = ROOT_DIR / 'data' / 'results' / f'pytorch_t{t_run}s_n{n_run}.parquet'
    if not expected_output.exists():
        # Fallback search if named differently
        files = list((ROOT_DIR / 'data' / 'results').glob("*.parquet"))
        if files:
            expected_output = files[-1]

    print(f"Simulation completed. Output file: {expected_output}")
    return expected_output


def run_pipeline(
    experiment: str = "sugar",
    t_run: float = 1.0,
    n_run: int = 1,
    skip_sim: bool = False,
    input_parquet: str = None,
    no_gui: bool = False,
    output_dir: str = "data/evaluation"
):
    # Step 1: Obtain simulation parquet
    if skip_sim and input_parquet:
        parquet_path = Path(input_parquet)
    else:
        parquet_path = run_simulation(experiment_name=experiment, t_run=t_run, n_run=n_run)

    if not parquet_path.exists():
        raise FileNotFoundError(f"Spike parquet not found at: {parquet_path}")

    # Step 2: Electrophysiological & Phenotype Analysis
    print("\n" + "=" * 70)
    print("STEP 2: Evaluating Nervous System Metrics & Phenotypic Trait Mapping")
    print("=" * 70)

    annot_path = ROOT_DIR / "data" / "flywire_annotations.tsv"
    out_eval = ROOT_DIR / output_dir
    report_html = generate_evaluation_report(
        parquet_path=parquet_path,
        annot_path=annot_path,
        output_dir=out_eval,
        report_name=f"report_{parquet_path.stem}"
    )

    print(f"\nEvaluation Complete! HTML Report: {report_html}")

    # Step 3: Launch Enhanced GUI (if not disabled)
    if not no_gui:
        print("\n" + "=" * 70)
        print("STEP 3: Launching Interactive Visualizer")
        print("=" * 70)
        import tkinter as tk
        from visualizer import FlyBrainVisualizer

        df_spikes = load_spike_data(parquet_path)
        df_annot = load_annotations(annot_path) if annot_path.exists() else None
        df_metrics = compute_neuron_metrics(df_spikes, df_annot)

        root = tk.Tk()
        app = FlyBrainVisualizer(root, df_spikes, df_metrics)
        root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="End-to-end Neural Electrophysiology & Simulation Pipeline")
    parser.add_argument("--experiment", type=str, default="sugar", choices=list(EXPERIMENTS.keys()),
                        help=f"Simulation stimulus experiment: {list(EXPERIMENTS.keys())}")
    parser.add_argument("--t_run", type=float, default=1.0, help="Simulation time in seconds (e.g., 0.1, 1, 10)")
    parser.add_argument("--n_run", type=int, default=1, help="Number of trials (default: 1)")
    parser.add_argument("--skip_sim", action="store_true", help="Skip simulation and use existing parquet")
    parser.add_argument("--input_parquet", type=str, default=None, help="Path to parquet if --skip_sim")
    parser.add_argument("--no_gui", action="store_true", help="Disable GUI visualizer (headless mode)")
    parser.add_argument("--output_dir", type=str, default="data/evaluation", help="Evaluation output dir")

    args = parser.parse_args()
    run_pipeline(
        experiment=args.experiment,
        t_run=args.t_run,
        n_run=args.n_run,
        skip_sim=args.skip_sim,
        input_parquet=args.input_parquet,
        no_gui=args.no_gui,
        output_dir=args.output_dir
    )


if __name__ == '__main__':
    main()
