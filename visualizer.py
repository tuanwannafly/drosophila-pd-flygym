"""
Drosophila Brain Activity Visualizer (Phase A Enhanced)
Interactive GUI to visualize spike propagation, phenotypic traits, and neuron electrophysiology.
"""

import sys
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path

from data_processing import load_spike_data, load_annotations, compute_neuron_metrics


class FlyBrainVisualizer:
    def __init__(self, root, df_spikes, df_metrics=None):
        self.root = root
        self.root.title("Drosophila Brain - Neural Activity & Phenotype Visualizer")
        self.root.configure(bg='#0a0a0a')
        self.root.state('zoomed')

        self.df = df_spikes
        self.df_metrics = df_metrics
        if self.df_metrics is not None and not self.df_metrics.empty:
            self.metrics_by_id = self.df_metrics.set_index('flywire_id').to_dict(orient='index')
        else:
            self.metrics_by_id = {}

        self.neurons = sorted(df_spikes['flywire_id'].unique())
        self.neuron_idx = {nid: i for i, nid in enumerate(self.neurons)}
        self.idx_to_neuron = {i: nid for i, nid in enumerate(self.neurons)}
        self.n_neurons = len(self.neurons)
        self.t_max = float(df_spikes['t'].max())
        self.t_min = float(df_spikes['t'].min())

        # Precompute spike times per neuron
        self.spike_times = {}
        for nid in self.neurons:
            self.spike_times[nid] = df_spikes[df_spikes['flywire_id'] == nid]['t'].values

        # Precompute binned firing rates
        self.bin_size = 5.0  # ms
        self.time_bins = np.arange(0, self.t_max + self.bin_size, self.bin_size)
        self.n_bins = len(self.time_bins) - 1

        # Activity matrix: neurons x time_bins
        self.activity_matrix = np.zeros((self.n_neurons, self.n_bins))
        for nid in self.neurons:
            idx = self.neuron_idx[nid]
            times = self.spike_times[nid]
            hist, _ = np.histogram(times, bins=self.time_bins)
            self.activity_matrix[idx] = hist

        # Sort neurons by total spike count for heatmap
        total_spikes = self.activity_matrix.sum(axis=1)
        self.sort_order = np.argsort(-total_spikes)
        self.activity_sorted = self.activity_matrix[self.sort_order]

        # Animation state
        self.playing = False
        self.current_bin = 0
        self.speed = 50  # ms per frame
        self.anim_id = None
        self.selected_nid = self.neurons[0] if self.n_neurons > 0 else None

        # Custom colormap: black -> blue -> cyan -> white
        colors = ['#0a0a0a', '#0d1b4a', '#1b4f8a', '#00b4d8', '#48cae4', '#90e0ef', '#ffffff']
        self.cmap = LinearSegmentedColormap.from_list('neural', colors, N=256)

        self._build_ui()

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Dark.TFrame', background='#0a0a0a')
        style.configure('Dark.TLabel', background='#0a0a0a', foreground='#48cae4',
                        font=('Consolas', 10))
        style.configure('Title.TLabel', background='#0a0a0a', foreground='#00b4d8',
                        font=('Consolas', 15, 'bold'))
        style.configure('Stat.TLabel', background='#0a0a0a', foreground='#90e0ef',
                        font=('Consolas', 11))
        style.configure('Card.TFrame', background='#141923', relief='ridge')
        style.configure('CardHeader.TLabel', background='#141923', foreground='#38bdf8',
                        font=('Consolas', 11, 'bold'))
        style.configure('CardText.TLabel', background='#141923', foreground='#e2e8f0',
                        font=('Consolas', 9))

        # Header
        header = ttk.Frame(self.root, style='Dark.TFrame')
        header.pack(fill='x', padx=10, pady=(8, 0))

        ttk.Label(header, text="DROSOPHILA WHOLE-BRAIN ACTIVITY & PHENOTYPE EXPLORER",
                  style='Title.TLabel').pack(side='left')

        stats_frame = ttk.Frame(header, style='Dark.TFrame')
        stats_frame.pack(side='right')
        ttk.Label(stats_frame, text=f"Active Neurons: {self.n_neurons:,}  |  "
                  f"Total Spikes: {len(self.df):,}  |  "
                  f"Duration: {self.t_max:.0f} ms",
                  style='Stat.TLabel').pack()

        # Body: Left = Figures (Raster, Heatmap, Pop rate), Right = Selected Neuron & Trait Info
        body_frame = ttk.Frame(self.root, style='Dark.TFrame')
        body_frame.pack(fill='both', expand=True, padx=10, pady=5)

        fig_frame = ttk.Frame(body_frame, style='Dark.TFrame')
        fig_frame.pack(side='left', fill='both', expand=True)

        self.fig = plt.Figure(figsize=(12, 8), facecolor='#0a0a0a')
        self.fig.subplots_adjust(hspace=0.35, left=0.06, right=0.97, top=0.95, bottom=0.08)

        # Subplot 1: Spike Raster
        self.ax_raster = self.fig.add_subplot(3, 1, 1)
        self._style_axis(self.ax_raster, "Spike Raster Plot (Click neuron to inspect)")

        # Subplot 2: Activity Heatmap
        self.ax_heatmap = self.fig.add_subplot(3, 1, 2)
        self._style_axis(self.ax_heatmap, "Neural Activity Heatmap (Ranked by spike count)")

        # Subplot 3: Population firing rate
        self.ax_rate = self.fig.add_subplot(3, 1, 3)
        self._style_axis(self.ax_rate, "Population Firing Rate (Spikes / 5ms bin)")

        self.canvas = FigureCanvasTkAgg(self.fig, master=fig_frame)
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        self.canvas.mpl_connect('button_press_event', self._on_plot_click)

        # Right Panel: Detailed Neuron & Phenotypic Trait Inspector
        side_panel = ttk.Frame(body_frame, style='Card.TFrame', width=300)
        side_panel.pack(side='right', fill='y', padx=(10, 0), ipadx=10, ipady=10)
        side_panel.pack_propagate(False)

        ttk.Label(side_panel, text="NEURON PHENOTYPE & METRICS", style='CardHeader.TLabel').pack(anchor='w', pady=(0, 10))

        self.lbl_neuron_id = ttk.Label(side_panel, text="ID: -", style='CardText.TLabel')
        self.lbl_neuron_id.pack(anchor='w', pady=2)

        self.lbl_cell_class = ttk.Label(side_panel, text="Class: -", style='CardText.TLabel')
        self.lbl_cell_class.pack(anchor='w', pady=2)

        self.lbl_cell_type = ttk.Label(side_panel, text="Type: -", style='CardText.TLabel')
        self.lbl_cell_type.pack(anchor='w', pady=2)

        self.lbl_nt = ttk.Label(side_panel, text="NT: -", style='CardText.TLabel')
        self.lbl_nt.pack(anchor='w', pady=2)

        self.lbl_spikes = ttk.Label(side_panel, text="Spikes: -", style='CardText.TLabel')
        self.lbl_spikes.pack(anchor='w', pady=2)

        self.lbl_fr = ttk.Label(side_panel, text="Firing Rate: - Hz", style='CardText.TLabel')
        self.lbl_fr.pack(anchor='w', pady=2)

        self.lbl_isi = ttk.Label(side_panel, text="ISI Mean: - ms", style='CardText.TLabel')
        self.lbl_isi.pack(anchor='w', pady=2)

        self.lbl_burst = ttk.Label(side_panel, text="Burst Ratio: -", style='CardText.TLabel')
        self.lbl_burst.pack(anchor='w', pady=2)

        # Quick select dropdown
        ttk.Label(side_panel, text="\nTop Active Neurons:", style='CardHeader.TLabel').pack(anchor='w', pady=(10, 5))
        self.top_dropdown_var = tk.StringVar()
        top_nids = [str(self.neurons[i]) for i in self.sort_order[:25]] if self.n_neurons > 0 else []
        self.top_dropdown = ttk.Combobox(side_panel, textvariable=self.top_dropdown_var, values=top_nids, state='readonly')
        self.top_dropdown.pack(fill='x', pady=5)
        self.top_dropdown.bind('<<ComboboxSelected>>', self._on_top_selected)

        # Controls (Bottom)
        controls = ttk.Frame(self.root, style='Dark.TFrame')
        controls.pack(fill='x', padx=10, pady=(0, 8))

        self.play_btn = tk.Button(controls, text="PLAY", command=self._toggle_play,
                                   bg='#1b4f8a', fg='white', font=('Consolas', 11, 'bold'),
                                   width=8, relief='flat', activebackground='#00b4d8')
        self.play_btn.pack(side='left', padx=5)

        tk.Button(controls, text="RESET", command=self._reset,
                  bg='#333', fg='white', font=('Consolas', 11),
                  width=8, relief='flat', activebackground='#555').pack(side='left', padx=5)

        ttk.Label(controls, text="Time:", style='Dark.TLabel').pack(side='left', padx=(20, 5))

        self.time_var = tk.DoubleVar(value=0)
        self.time_slider = tk.Scale(controls, from_=0, to=self.n_bins - 1,
                                     orient='horizontal', variable=self.time_var,
                                     command=self._on_slider, showvalue=False,
                                     bg='#0a0a0a', fg='#48cae4', troughcolor='#1b4f8a',
                                     highlightthickness=0, length=450)
        self.time_slider.pack(side='left', fill='x', expand=True, padx=5)

        self.time_label = ttk.Label(controls, text="0.0 ms", style='Stat.TLabel')
        self.time_label.pack(side='left', padx=10)

        self.spike_label = ttk.Label(controls, text="Active: 0", style='Stat.TLabel')
        self.spike_label.pack(side='left', padx=10)

        # Draw initial plots
        self._draw_static()
        self._update_frame(0)
        if self.selected_nid:
            self._update_neuron_panel(self.selected_nid)

    def _style_axis(self, ax, title):
        ax.set_facecolor('#0a0a0a')
        ax.set_title(title, color='#48cae4', fontsize=10, fontfamily='monospace', pad=6)
        ax.tick_params(colors='#666', labelsize=8)
        for spine in ax.spines.values():
            spine.set_color('#333')

    def _draw_static(self):
        ax = self.ax_raster
        ax.clear()
        self._style_axis(ax, "Spike Raster Plot (Click neuron to inspect)")

        # Color-code spikes by neurotransmitter if available
        for nid in self.neurons:
            y = self.neuron_idx[nid]
            times = self.spike_times[nid]
            color = '#00b4d8'
            if nid in self.metrics_by_id:
                nt = self.metrics_by_id[nid].get('top_nt', '')
                if nt == 'acetylcholine':
                    color = '#38bdf8'
                elif nt == 'glutamate':
                    color = '#4ade80'
                elif nt == 'gaba':
                    color = '#f87171'
            ax.scatter(times, np.full_like(times, y), s=0.5, c=color, alpha=0.7, linewidths=0)

        ax.set_xlim(0, self.t_max)
        ax.set_ylim(-1, self.n_neurons)
        ax.set_ylabel('Neuron Index', color='#888', fontsize=9)
        self.raster_line = ax.axvline(x=0, color='#ff4444', linewidth=1, alpha=0.8)

        # Heatmap
        ax2 = self.ax_heatmap
        ax2.clear()
        self._style_axis(ax2, "Neural Activity Heatmap (Ranked by spike count)")

        n_show = min(80, self.n_neurons)
        display_data = self.activity_sorted[:n_show]
        vmax = max(display_data.max(), 1)

        self.heatmap_img = ax2.imshow(
            display_data, aspect='auto', cmap=self.cmap,
            extent=[0, self.t_max, n_show, 0],
            vmin=0, vmax=vmax, interpolation='nearest'
        )
        ax2.set_ylabel('Neuron Rank', color='#888', fontsize=9)
        self.heatmap_line = ax2.axvline(x=0, color='#ff4444', linewidth=1, alpha=0.8)

        # Population rate
        ax3 = self.ax_rate
        ax3.clear()
        self._style_axis(ax3, "Population Firing Rate (Spikes / 5ms bin)")

        pop_rate = self.activity_matrix.sum(axis=0)
        bin_centers = (self.time_bins[:-1] + self.time_bins[1:]) / 2

        ax3.fill_between(bin_centers, pop_rate, alpha=0.3, color='#00b4d8')
        ax3.plot(bin_centers, pop_rate, color='#48cae4', linewidth=0.8)
        ax3.set_xlim(0, self.t_max)
        ax3.set_ylim(0, max(pop_rate.max() * 1.1, 1))
        ax3.set_xlabel('Time (ms)', color='#888', fontsize=9)
        ax3.set_ylabel('Spikes', color='#888', fontsize=9)
        self.rate_line = ax3.axvline(x=0, color='#ff4444', linewidth=1, alpha=0.8)

        self.canvas.draw()

    def _update_frame(self, bin_idx):
        bin_idx = int(bin_idx)
        t_ms = self.time_bins[bin_idx]

        self.raster_line.set_xdata([t_ms, t_ms])
        self.heatmap_line.set_xdata([t_ms, t_ms])
        self.rate_line.set_xdata([t_ms, t_ms])

        self.time_label.config(text=f"{t_ms:.0f} ms")

        if bin_idx < self.n_bins:
            active = int((self.activity_matrix[:, bin_idx] > 0).sum())
            spikes_now = int(self.activity_matrix[:, bin_idx].sum())
        else:
            active = 0
            spikes_now = 0
        self.spike_label.config(text=f"Active: {active} | Spikes: {spikes_now}")

        self.canvas.draw_idle()

    def _on_plot_click(self, event):
        if event.inaxes == self.ax_raster and event.ydata is not None:
            y_idx = int(round(event.ydata))
            if 0 <= y_idx < self.n_neurons:
                nid = self.idx_to_neuron[y_idx]
                self._update_neuron_panel(nid)

    def _on_top_selected(self, event):
        val = self.top_dropdown_var.get()
        if val:
            self._update_neuron_panel(int(val))

    def _update_neuron_panel(self, nid: int):
        self.selected_nid = nid
        m = self.metrics_by_id.get(nid, {})

        self.lbl_neuron_id.config(text=f"ID: {nid}")
        self.lbl_cell_class.config(text=f"Class: {m.get('super_class', 'N/A')}")
        self.lbl_cell_type.config(text=f"Type: {m.get('cell_type', 'N/A')}")
        self.lbl_nt.config(text=f"NT: {m.get('top_nt', 'N/A')}")
        self.lbl_spikes.config(text=f"Spikes: {m.get('spike_count', len(self.spike_times.get(nid, []))):,}")
        
        fr = m.get('firing_rate_hz')
        self.lbl_fr.config(text=f"Firing Rate: {fr:.2f} Hz" if pd.notna(fr) else "Firing Rate: N/A")
        
        isi = m.get('isi_mean_ms')
        self.lbl_isi.config(text=f"ISI Mean: {isi:.2f} ms" if pd.notna(isi) else "ISI Mean: N/A")
        
        br = m.get('burst_ratio')
        self.lbl_burst.config(text=f"Burst Ratio: {br:.2f}" if pd.notna(br) else "Burst Ratio: N/A")

    def _on_slider(self, val):
        self._update_frame(float(val))

    def _toggle_play(self):
        if self.playing:
            self.playing = False
            self.play_btn.config(text="PLAY", bg='#1b4f8a')
            if self.anim_id:
                self.root.after_cancel(self.anim_id)
        else:
            self.playing = True
            self.play_btn.config(text="PAUSE", bg='#ff4444')
            self._animate()

    def _animate(self):
        if not self.playing:
            return
        self.current_bin = int(self.time_var.get()) + 1
        if self.current_bin >= self.n_bins:
            self.current_bin = 0
        self.time_var.set(self.current_bin)
        self._update_frame(self.current_bin)
        self.anim_id = self.root.after(self.speed, self._animate)

    def _reset(self):
        self.playing = False
        self.play_btn.config(text="PLAY", bg='#1b4f8a')
        if self.anim_id:
            self.root.after_cancel(self.anim_id)
        self.current_bin = 0
        self.time_var.set(0)
        self._update_frame(0)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Phase A Visualizer with Phenotypes & Metrics")
    parser.add_argument("--parquet", type=str, default=None, help="Path to simulation spike parquet")
    parser.add_argument("--annot", type=str, default="data/flywire_annotations.tsv", help="Path to annotations TSV")
    args = parser.parse_args()

    parquet_path = Path(args.parquet) if args.parquet else (Path(__file__).parent / 'data' / 'results' / 'pytorch_t1.0s_n1.parquet')

    if not parquet_path.exists():
        print(f"No simulation data found at {parquet_path}")
        print("Run the pipeline first: python pipeline.py --t_run 1.0 --experiment sugar")
        return

    print("Loading simulation spike data...")
    df_spikes = load_spike_data(parquet_path)
    
    annot_path = Path(args.annot)
    df_annot = load_annotations(annot_path) if annot_path.exists() else None

    print("Calculating neuron electrophysiology and phenotype mappings...")
    df_metrics = compute_neuron_metrics(df_spikes, df_annot)

    print("Launching enhanced visualizer...")
    root = tk.Tk()
    app = FlyBrainVisualizer(root, df_spikes, df_metrics)
    root.mainloop()


if __name__ == '__main__':
    main()
