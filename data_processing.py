"""
Data Processing and Feature Extraction for Drosophila Neural Simulations.
Computes neuron-level metrics, functional connectivity metrics, and integrates
FlyWire cell annotations (phenotypes/traits) without requiring body/motion data.
"""

from pathlib import Path
from typing import Optional, Dict, Tuple, Union
import numpy as np
import pandas as pd


def load_annotations(tsv_path: Union[str, Path]) -> pd.DataFrame:
    """
    Loads FlyWire annotations TSV and cleans relevant phenotype/trait columns.
    """
    tsv_path = Path(tsv_path)
    if not tsv_path.exists():
        raise FileNotFoundError(f"Annotations file not found: {tsv_path}")
    
    usecols = [
        'root_id', 'super_class', 'cell_class', 'cell_type',
        'top_nt', 'top_nt_conf', 'side', 'dimorphism', 'fru_dsx'
    ]
    df_annot = pd.read_csv(tsv_path, sep='\t', usecols=lambda c: c in usecols)
    df_annot.rename(columns={'root_id': 'flywire_id'}, inplace=True)
    df_annot['flywire_id'] = df_annot['flywire_id'].astype(np.int64)
    return df_annot


def load_spike_data(parquet_path: Union[str, Path]) -> pd.DataFrame:
    """
    Loads spike dataframe from parquet file.
    Expected columns: 'flywire_id', 't' (ms), and optionally 'trial' / 'run'.
    """
    parquet_path = Path(parquet_path)
    if not parquet_path.exists():
        raise FileNotFoundError(f"Spike parquet file not found: {parquet_path}")
    
    df = pd.read_parquet(parquet_path)
    if 'flywire_id' not in df.columns or 't' not in df.columns:
        raise ValueError(f"Parquet missing required columns ('flywire_id', 't'). Found: {df.columns.tolist()}")
    return df


def compute_neuron_metrics(
    df_spikes: pd.DataFrame,
    df_annot: Optional[pd.DataFrame] = None,
    t_min: Optional[float] = None,
    t_max: Optional[float] = None,
    burst_isi_thresh_ms: float = 10.0
) -> pd.DataFrame:
    """
    Computes neuron-level electrophysiological properties and integrates traits:
      - spike_count: Total spikes
      - firing_rate_hz: Mean firing rate over recording duration (Hz)
      - isi_mean_ms: Mean inter-spike interval
      - isi_cv: Coefficient of variation of ISI (burstiness / regularity)
      - burst_spikes: Number of spikes occurring within short ISIs (< threshold)
      - burst_ratio: Fraction of spikes in bursts
      - first_spike_t: Latency to first spike (ms)
      - last_spike_t: Time of last spike (ms)
    """
    if len(df_spikes) == 0:
        return pd.DataFrame(columns=[
            'flywire_id', 'spike_count', 'firing_rate_hz', 'isi_mean_ms',
            'isi_cv', 'burst_spikes', 'burst_ratio', 'first_spike_t', 'last_spike_t'
        ])

    if t_min is None:
        t_min = float(df_spikes['t'].min())
    if t_max is None:
        t_max = float(df_spikes['t'].max())

    duration_sec = max((t_max - t_min) / 1000.0, 1e-6)

    metrics_list = []
    # Group spikes per neuron
    grouped = df_spikes.groupby('flywire_id')

    for nid, group in grouped:
        times = np.sort(group['t'].values)
        n_spikes = len(times)
        fr_hz = n_spikes / duration_sec
        first_t = float(times[0])
        last_t = float(times[-1])

        if n_spikes > 1:
            isis = np.diff(times)
            isi_mean = float(np.mean(isis))
            isi_std = float(np.std(isis))
            isi_cv = float(isi_std / isi_mean) if isi_mean > 0 else 0.0
            burst_mask = isis <= burst_isi_thresh_ms
            burst_spikes = int(np.sum(burst_mask) + (1 if np.any(burst_mask) else 0))
            burst_ratio = float(burst_spikes / n_spikes)
        else:
            isi_mean = np.nan
            isi_cv = np.nan
            burst_spikes = 0
            burst_ratio = 0.0

        metrics_list.append({
            'flywire_id': nid,
            'spike_count': n_spikes,
            'firing_rate_hz': fr_hz,
            'isi_mean_ms': isi_mean,
            'isi_cv': isi_cv,
            'burst_spikes': burst_spikes,
            'burst_ratio': burst_ratio,
            'first_spike_t': first_t,
            'last_spike_t': last_t
        })

    df_metrics = pd.DataFrame(metrics_list)

    # Merge annotations / phenotypic traits if available
    if df_annot is not None and len(df_metrics) > 0:
        df_metrics = df_metrics.merge(df_annot, on='flywire_id', how='left')

    return df_metrics


def compute_population_metrics(
    df_spikes: pd.DataFrame,
    bin_size_ms: float = 5.0,
    t_min: Optional[float] = None,
    t_max: Optional[float] = None
) -> Dict[str, Union[float, int, np.ndarray]]:
    """
    Computes global nervous-system level metrics across time:
      - total_spikes, total_active_neurons
      - time_bins, population_rate_binned
      - synchrony_fano_factor: Variance/mean of population binned count
      - network_firing_rate_hz: Total spikes / (N_active * duration)
    """
    if len(df_spikes) == 0:
        return {
            'total_spikes': 0,
            'total_active_neurons': 0,
            'duration_ms': 0.0,
            'mean_pop_rate_hz': 0.0,
            'fano_factor': 0.0
        }

    if t_min is None:
        t_min = float(df_spikes['t'].min())
    if t_max is None:
        t_max = float(df_spikes['t'].max())

    bins = np.arange(t_min, t_max + bin_size_ms, bin_size_ms)
    counts, _ = np.histogram(df_spikes['t'].values, bins=bins)

    n_active = df_spikes['flywire_id'].nunique()
    duration_sec = max((t_max - t_min) / 1000.0, 1e-6)
    total_spikes = len(df_spikes)

    # Fano factor across time bins as a measure of burstiness/synchrony
    mean_count = np.mean(counts) if len(counts) > 0 else 0
    var_count = np.var(counts) if len(counts) > 0 else 0
    fano_factor = float(var_count / mean_count) if mean_count > 0 else 0.0

    return {
        'total_spikes': total_spikes,
        'total_active_neurons': n_active,
        'duration_ms': t_max - t_min,
        'time_bins': bins,
        'pop_binned_counts': counts,
        'mean_pop_count_per_bin': float(mean_count),
        'fano_factor': fano_factor,
        'global_firing_rate_hz': float(total_spikes / (n_active * duration_sec)) if n_active > 0 else 0.0
    }
