"""
Dataset Evaluation and Comprehensive Report Generator for Drosophila Neural Activity.
Generates full nervous system and neuron-level electrophysiological evaluation reports.
"""

import sys
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add parent path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data_processing import (
    load_spike_data, load_annotations, compute_neuron_metrics, compute_population_metrics
)


def generate_evaluation_report(
    parquet_path: Path,
    annot_path: Path,
    output_dir: Path,
    report_name: str = "neural_evaluation_report"
):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading spike data: {parquet_path}")
    df_spikes = load_spike_data(parquet_path)
    
    print(f"Loading annotations: {annot_path}")
    df_annot = load_annotations(annot_path) if annot_path and annot_path.exists() else None

    print("Computing neuron electrophysiological & trait metrics...")
    df_metrics = compute_neuron_metrics(df_spikes, df_annot)
    pop_metrics = compute_population_metrics(df_spikes)

    # Save metrics table
    csv_metrics_path = output_dir / f"{report_name}_neuron_metrics.csv"
    df_metrics.to_csv(csv_metrics_path, index=False)
    print(f"Saved neuron metrics CSV: {csv_metrics_path}")

    # Set dark aesthetic for figures
    plt.style.use('dark_background')

    # 1. Firing Rate Distribution Plot
    fig1, ax1 = plt.subplots(figsize=(8, 4.5))
    if len(df_metrics) > 0 and 'firing_rate_hz' in df_metrics.columns:
        ax1.hist(df_metrics['firing_rate_hz'], bins=30, color='#00b4d8', edgecolor='#0a0a0a', alpha=0.85)
        ax1.set_title("Neuron Firing Rate Distribution (Hz)", color='#48cae4', fontsize=12)
        ax1.set_xlabel("Firing Rate (Hz)", color='#aaaaaa')
        ax1.set_ylabel("Neuron Count", color='#aaaaaa')
        ax1.grid(True, alpha=0.2, linestyle='--')
    fig1.tight_layout()
    fig1_path = figures_dir / "firing_rate_dist.png"
    fig1.savefig(fig1_path, dpi=200)
    plt.close(fig1)

    # 2. Burst Ratio vs Firing Rate
    fig2, ax2 = plt.subplots(figsize=(8, 4.5))
    if len(df_metrics) > 0 and 'burst_ratio' in df_metrics.columns:
        scatter = ax2.scatter(
            df_metrics['firing_rate_hz'],
            df_metrics['burst_ratio'],
            c=df_metrics['isi_cv'].fillna(0),
            cmap='plasma',
            alpha=0.7,
            s=25
        )
        cbar = plt.colorbar(scatter, ax=ax2)
        cbar.set_label('ISI CV (Regularity/Burstiness)', color='#aaaaaa')
        cbar.ax.yaxis.set_tick_params(color='#aaaaaa')
        ax2.set_title("Burst Ratio vs. Mean Firing Rate", color='#48cae4', fontsize=12)
        ax2.set_xlabel("Firing Rate (Hz)", color='#aaaaaa')
        ax2.set_ylabel("Burst Ratio (ISIs ≤ 10ms)", color='#aaaaaa')
        ax2.grid(True, alpha=0.2, linestyle='--')
    fig2.tight_layout()
    fig2_path = figures_dir / "burst_vs_rate.png"
    fig2.savefig(fig2_path, dpi=200)
    plt.close(fig2)

    # 3. Super-class / Cell-class Activity Breakdown (if annotation available)
    fig3_path = None
    if 'super_class' in df_metrics.columns and df_metrics['super_class'].dropna().nunique() > 0:
        fig3, ax3 = plt.subplots(figsize=(10, 5))
        class_summary = df_metrics.groupby('super_class')['spike_count'].sum().sort_values(ascending=False)
        class_summary.plot(kind='bar', ax=ax3, color='#48cae4', edgecolor='#0a0a0a')
        ax3.set_title("Spike Count by Super Class / Neural Subsystem", color='#48cae4', fontsize=12)
        ax3.set_ylabel("Total Spikes", color='#aaaaaa')
        ax3.set_xlabel("Super Class", color='#aaaaaa')
        plt.xticks(rotation=45, ha='right')
        ax3.grid(True, alpha=0.2, linestyle='--')
        fig3.tight_layout()
        fig3_path = figures_dir / "super_class_spikes.png"
        fig3.savefig(fig3_path, dpi=200)
        plt.close(fig3)

    # 4. Neurotransmitter Distribution
    fig4_path = None
    if 'top_nt' in df_metrics.columns and df_metrics['top_nt'].dropna().nunique() > 0:
        fig4, ax4 = plt.subplots(figsize=(8, 4.5))
        nt_summary = df_metrics.groupby('top_nt')['spike_count'].sum().sort_values(ascending=False)
        nt_summary.plot(kind='bar', ax=ax4, color='#90e0ef', edgecolor='#0a0a0a')
        ax4.set_title("Neural Spikes by Neurotransmitter (NT Expression)", color='#48cae4', fontsize=12)
        ax4.set_ylabel("Total Spikes", color='#aaaaaa')
        ax4.set_xlabel("Neurotransmitter", color='#aaaaaa')
        plt.xticks(rotation=30, ha='right')
        ax4.grid(True, alpha=0.2, linestyle='--')
        fig4.tight_layout()
        fig4_path = figures_dir / "nt_expression_spikes.png"
        fig4.savefig(fig4_path, dpi=200)
        plt.close(fig4)

    # Build HTML Report
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Drosophila Neural System Evaluation Report</title>
    <style>
        body {{
            background-color: #0b0f19;
            color: #e2e8f0;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            margin: 0;
            padding: 30px;
        }}
        h1, h2, h3 {{
            color: #38bdf8;
        }}
        .metric-card-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .card {{
            background: #1e293b;
            padding: 18px;
            border-radius: 8px;
            border-left: 4px solid #38bdf8;
        }}
        .card-title {{
            font-size: 12px;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .card-value {{
            font-size: 24px;
            font-weight: bold;
            color: #f8fafc;
            margin-top: 5px;
        }}
        .figures-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .fig-box {{
            background: #1e293b;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .fig-box img {{
            max-width: 100%;
            border-radius: 4px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: #1e293b;
            border-radius: 8px;
            overflow: hidden;
        }}
        th, td {{
            padding: 10px 14px;
            text-align: left;
            border-bottom: 1px solid #334155;
            font-size: 13px;
        }}
        th {{
            background: #0f172a;
            color: #38bdf8;
        }}
    </style>
</head>
<body>
    <h1>🔬 Drosophila Nervous System Electrophysiology & Phenotype Report</h1>
    <p>Target Dataset: <code>{parquet_path.name}</code></p>
    
    <h2>1. Global Neural System Metrics</h2>
    <div class="metric-card-grid">
        <div class="card">
            <div class="card-title">Active Neurons</div>
            <div class="card-value">{pop_metrics['total_active_neurons']:,}</div>
        </div>
        <div class="card">
            <div class="card-title">Total Spikes</div>
            <div class="card-value">{pop_metrics['total_spikes']:,}</div>
        </div>
        <div class="card">
            <div class="card-title">Recording Duration</div>
            <div class="card-value">{pop_metrics['duration_ms']:.1f} ms</div>
        </div>
        <div class="card">
            <div class="card-title">Network Firing Rate</div>
            <div class="card-value">{pop_metrics['global_firing_rate_hz']:.2f} Hz</div>
        </div>
        <div class="card">
            <div class="card-title">Synchrony (Fano Factor)</div>
            <div class="card-value">{pop_metrics['fano_factor']:.2f}</div>
        </div>
    </div>

    <h2>2. Visual Electrophysiology & Trait Profiling</h2>
    <div class="figures-grid">
        <div class="fig-box">
            <h3>Firing Rate Distribution</h3>
            <img src="figures/{fig1_path.name}" alt="Firing Rate Distribution">
        </div>
        <div class="fig-box">
            <h3>Burst Ratio vs. Mean Firing Rate</h3>
            <img src="figures/{fig2_path.name}" alt="Burst Dynamics">
        </div>
        {f'''<div class="fig-box">
            <h3>Subsystem / Super-class Activity</h3>
            <img src="figures/{fig3_path.name}" alt="Super Class Distribution">
        </div>''' if fig3_path else ''}
        {f'''<div class="fig-box">
            <h3>Neurotransmitter Expression Dynamics</h3>
            <img src="figures/{fig4_path.name}" alt="Neurotransmitter Distribution">
        </div>''' if fig4_path else ''}
    </div>

    <h2>3. Top 15 Most Active Neurons & Traits</h2>
    <table>
        <thead>
            <tr>
                <th>FlyWire ID</th>
                <th>Cell Type</th>
                <th>Super Class</th>
                <th>Top NT</th>
                <th>Spike Count</th>
                <th>Firing Rate (Hz)</th>
                <th>ISI Mean (ms)</th>
                <th>Burst Ratio</th>
            </tr>
        </thead>
        <tbody>
"""
    top_neurons = df_metrics.sort_values(by='spike_count', ascending=False).head(15)
    for _, row in top_neurons.iterrows():
        html_content += f"""
            <tr>
                <td><code>{int(row['flywire_id'])}</code></td>
                <td>{row.get('cell_type', 'N/A')}</td>
                <td>{row.get('super_class', 'N/A')}</td>
                <td>{row.get('top_nt', 'N/A')}</td>
                <td>{int(row['spike_count']):,}</td>
                <td>{row['firing_rate_hz']:.2f}</td>
                <td>{row['isi_mean_ms']:.2f if pd.notna(row['isi_mean_ms']) else 'N/A'}</td>
                <td>{row['burst_ratio']:.2f}</td>
            </tr>
        """

    html_content += """
        </tbody>
    </table>
</body>
</html>
"""
    report_html_path = output_dir / f"{report_name}.html"
    report_html_path.write_text(html_content, encoding='utf-8')
    print(f"Generated HTML evaluation report: {report_html_path}")
    return report_html_path


def main():
    parser = argparse.ArgumentParser(description="Evaluate Drosophila neural simulation dataset")
    parser.add_argument("parquet_path", type=str, help="Path to simulation spike parquet")
    parser.add_argument("--annot", type=str, default="data/flywire_annotations.tsv", help="Path to annotations TSV")
    parser.add_argument("--output_dir", type=str, default="data/evaluation", help="Directory to store evaluation report")
    parser.add_argument("--name", type=str, default="neural_evaluation_report", help="Report name")

    args = parser.parse_args()
    generate_evaluation_report(
        parquet_path=Path(args.parquet_path),
        annot_path=Path(args.annot),
        output_dir=Path(args.output_dir),
        report_name=args.name
    )


if __name__ == '__main__':
    main()
